# coding: utf-8
"""
Data structures and functions for tracking units/cost history of financial assets.
Besides the fundamental requirement of keeping accurate tallies, the main purpose
of this module is to match opening and closing transactions in order to calculate
the amount and character of realized gains.

The basic way to use this module is to create a Portfolio instance, then pass
Transaction instances to its processTransaction() method.

Each Lot tracks the current state of a particular bunch of securities - (unit, cost).

Additionally, each Lot keeps a reference to its opening Transaction, i.e. the
Transaction which started its holding period for tax purposes (to determine whether
the character of realized Gains are long-term or short-term).

Lots are collected in sequences called "positions", which are the values of a
Portfolio mapping keyed by a (FI account, security) called a "pocket".

Each Lot keeps a reference to its "creating" Transaction, i.e. the Transaction which
added the Lot to its current pocket.  In the case of an opening trade, the
opening Transaction and the creating Transaction will be the same.  In the case of
of a transfer, spin-off, reorg, etc., these will be different; the date of the tax
holding period can be sourced from the opening Transaction, while the current
pocket can be sourced from the creating Transaction.

Gains link opening Transactions to realizing Transactions - which are usually closing
Transactions, but may also come from return of capital distributions that exceed
cost basis.  Return of capital Transactions generally don't provide per-share
distribution information, so Gains must keep state for the realizing price.

Lots and Transactions are immutable, so you can rely on the accuracy of references
to them (e.g. Gain.lot & Gain.transaction).  Everything about a Lot (except
opentransaction) can be changed by Transactions; the changes are reflected in a
newly-created Lot, leaving the old Lot undisturbed.

Nothing in this module changes a Transaction or a Gain, once created.
"""
# stdlib imports
from collections import (namedtuple, defaultdict)
from decimal import Decimal
from datetime import (date, timedelta)

# local import
from capgains import CONFIG
from capgains.models.transactions import CurrencyRate


###############################################################################
# BASIC DATA CONTAINERS
###############################################################################
Lot = namedtuple('Lot', ['opentransaction', 'createtransaction', 'units',
                         'price', 'currency'])
Lot.__doc__ += ': Cost basis/holding data container'
Lot.opentransaction.__doc__ = 'Transaction instance that began holding period'
Lot.createtransaction.__doc__ = ('Transaction instance that created the Lot '
                                 'for the current Position')
Lot.units.__doc__ = '(type decimal.Decimal; nonzero)'
Lot.price.__doc__ = 'Per-unit cost (type decimal.Decimal; positive or zero)'
Lot.currency.__doc__ = 'Currency denomination of cost price'


Gain = namedtuple('Gain', ['lot', 'transaction', 'price'])
Gain.lot.__doc__ = 'Lot instance for which gain is realized'
Gain.transaction.__doc__ = 'The Transaction instance realizing gain'
Gain.price.__doc__ = '(type decimal.Decimal; positive or zero)'


###############################################################################
# TRANSACTION MODEL
# Persistent SQL implementation of this model in capgains.models.transactions
###############################################################################
Transaction = namedtuple('Transaction', [
    'id', 'uniqueid', 'datetime', 'dtsettle', 'type', 'memo', 'currency',
    'cash', 'fiaccount', 'security', 'units', 'securityPrice', 'fiaccountFrom',
    'securityFrom', 'unitsFrom', 'securityFromPrice', 'numerator',
    'denominator', 'sort'])
Transaction.id.__doc__ = 'Local transaction unique identifer (database PK)'
Transaction.uniqueid.__doc__ = 'FI transaction unique identifier (type str)'
Transaction.datetime.__doc__ = 'Effective date/time (type datetime.datetime)'
Transaction.dtsettle.__doc__ = ('For cash distributions: payment date (dttrade'
                                ' is accrual date i.e. ex-date')
Transaction.type.__doc__ = ''
Transaction.memo.__doc__ = 'Transaction notes (type str)'
Transaction.currency.__doc__ = ('Currency denomination of Transaction.cash '
                                '(type str; ISO 4217)')
Transaction.cash.__doc__ = ('Change in money amount caused by Transaction '
                            '(type decimal.Decimal)')
Transaction.fiaccount.__doc__ = 'Financial institution acount'
Transaction.security.__doc__ = 'Security or other asset'
Transaction.units.__doc__ = ('Change in Security quantity caused by '
                             'Transaction (type decimal.Decimal)')
Transaction.fiaccountFrom.__doc__ = 'For transfers: source FI acount'
Transaction.securityFrom.__doc__ = ('For transfers, spinoffs, exercise: '
                                    'source Security')
Transaction.unitsFrom.__doc__ = ('For splits, transfers, exercise: change in '
                                 'quantity of source Security caused by '
                                 'Transaction (type decimal.Decimal)')
Transaction.securityPrice.__doc__ = ('For spinoffs: FMV of destination '
                                     'Security post-spin')
Transaction.securityFromPrice.__doc__ = ('For spinoffs: FMV of source '
                                         'security post-spin')
Transaction.numerator.__doc__ = ('For splits, spinoffs: normalized units of '
                                 'destination Security')
Transaction.denominator.__doc__ = ('For splits, spinoff: normalized units of '
                                   'source Security')
Transaction.sort.__doc__ = 'Sort algorithm for gain recognition'
Transaction.__new__.__defaults__ = (None, ) * 19


###############################################################################
# ERRORS
##############################################################################
class InventoryError(Exception):
    """ Base class for Exceptions defined in this module """
    pass


class Inconsistent(InventoryError):
    """
    Exception raised when Position's state is inconsistent with Transaction
    """
    def __init__(self, transaction, msg):
        self.transaction = transaction
        self.msg = msg
        super(Inconsistent, self).__init__(f"{transaction} inconsistent: {msg}")


###############################################################################
# FUNCTIONS OPERATING ON LOTS
###############################################################################
def part_lot(lot, units):
    """
    Partition Lot at specified # of units, adding new Lot of leftover units.

    Args: lot - Lot instance
          units - # of units to partition

    Returns: 2-tuple of Lots
    """
    if not isinstance(units, Decimal):
        raise ValueError(f"units must be type decimal.Decimal, not '{units}'")
    if not abs(units) < abs(lot.units):
        msg = f"units={units} must have smaller magnitude than lot.units={lot.units}"
        raise ValueError(msg)
    if not units * lot.units > 0:
        msg = f"units={units} and lot.units={lot.units} must have same sign (non-zero)"
        raise ValueError(msg)
    return (lot._replace(units=units), lot._replace(units=lot.units - units))


def take_lots(lots, criterion=None, max_units=None):
    """
    Remove a selection of Lots from the Position in sequential order.

    Sign convention is SAME SIGN as position, i.e. units arg must be
    positive for long, negative for short

    Args: lots - sequence of Lot instances (PRESORTED BY CALLER)
          criterion - filter function that accepts Lot instance as arg
          max_units - max units to take.  If units=None, take all units that
                      match criterion.

    Returns: 2-tuple of -
            * list of Lots matching criterion/units
            * list of other Lots
    """
    assert max_units is None or isinstance(max_units, Decimal)

    if criterion is None:
        def criterion(lot):
            return True

    lots_taken = []
    lots_left = []
    units_remain = max_units

    for lot in lots:
        if not criterion(lot):
            lots_left.append(lot)
        else:
            if units_remain is None:
                lots_taken.append(lot)
            elif units_remain == 0:
                lots_left.append(lot)
            elif abs(lot.units) <= abs(units_remain):
                if not lot.units * units_remain > 0:
                    msg = (f"units_remain={units_remain} and Lot.units={lot.units} "
                           "must have same sign (nonzero)")
                    raise Inconsistent(None, msg)

                lots_taken.append(lot)
                units_remain -= lot.units
            else:
                if not lot.units * units_remain > 0:
                    msg = (f"units_remain={units_remain} and Lot.units={lot.units} "
                           "must have same sign (nonzero)")
                    raise Inconsistent(None, msg)

                taken, left = part_lot(lot, units_remain)
                lots_taken.append(taken)
                units_remain -= taken.units
                lots_left.append(left)

    return lots_taken, lots_left


def take_basis(lots, criterion, fraction):
    """
    Remove a fraction of the cost from each Lot in the Position.

    Args: lots - sequence of Lot instances (PRESORTED BY CALLER)
          criterion - filter function that accepts Lot instance as arg
          fraction - portion of cost to take.

    Returns: 2-tuple of -
            0) list of Lots (copies of Lots meeting criterion, with each
               price updated to reflect the basis removed)
            1) list of Lots (original position, less basis removed)
    """
    if criterion is None:
        def criterion(lot):
            return True

    if not (0 <= fraction <= 1):
        msg = f"fraction must be between 0 and 1 (inclusive), not '{fraction}'"
        raise ValueError(msg)

    lots_taken = []
    lots_left = []

    for lot in lots:
        if criterion(lot):
            takenprice = lot.price * fraction
            lots_taken.append(lot._replace(price=takenprice))
            lots_left.append(lot._replace(price=lot.price - takenprice))
        else:
            lots_left.append(lot)

    return lots_taken, lots_left


###############################################################################
# PORTFOLIO
###############################################################################
class Portfolio(defaultdict):
    """
    Mapping container for positions (i.e. sequences of Lots),
    keyed by (FI account, security) a/k/a "pocket".
    """
    default_factory = list

    def __init__(self, *args, **kwargs):
        args = (self.default_factory, ) + args
        defaultdict.__init__(self, *args, **kwargs)

    def trade(self, transaction, opentransaction=None, createtransaction=None,
              sort=None):
        """
        Normal buy or sell, closing open Lots and realizing Gains.

        Args: transaction - a Transaction instance
              opentransaction - a Transaction instance; if present, overrides
                                lot.opentransaction to preserve holding period
              createtransaction - a Transaction instance; if present, overrides
                                  lot.createtransaction and gain.transaction
              sort - a 2-tuple of (key func, reverse) such as FIFO/MINGAIN etc.
                     defined above, used to order Lots when closing them.

        Returns: a list of Gain instances
        """
        self._validate_args(transaction,
                            units=Decimal, cash=(type(None), Decimal))
        if transaction.units == 0:
            raise ValueError(f"units can't be zero: {transaction}")

        pocket = (transaction.fiaccount, transaction.security)
        position = self[pocket]
        sort = sort or FIFO
        position.sort(**sort)

        try:
            lots_closed, position = take_lots(position,
                                              closableBy(transaction),
                                              -transaction.units)
        except Inconsistent as err:
            # Lot.units opposite sign from Transaction.units
            raise Inconsistent(transaction, err.msg)

        units = transaction.units + sum([lot.units for lot in lots_closed])
        price = abs(transaction.cash / transaction.units)
        if units != 0:
            position.append(
                Lot(opentransaction=opentransaction or transaction,
                    createtransaction=createtransaction or transaction,
                    units=units, price=price,
                    currency=transaction.currency))

        self[pocket] = position

        gains = [Gain(lot=lot, transaction=createtransaction or transaction,
                      price=price) for lot in lots_closed]
        return gains

    def returnofcapital(self, transaction, sort=None):
        """
        Apply cash to reduce Lot cost basis; realize Gain once basis has been
        reduced to zero.
        """
        self._validate_args(transaction, cash=Decimal)

        pocket = (transaction.fiaccount, transaction.security)
        position = self[pocket]

        # First get a total of shares affected by return of capital,
        # in order to determine RoC per share
        affected = list(filter(longAsOf(transaction.datetime), position))
        units = sum([lot.units for lot in affected])
        if units == 0:
            msg = (f"No long position for {transaction.fiaccount} in "
                   f"{transaciton.security} as of {transaction.datetime}")
            raise Inconsistent(transaction, msg)
        priceDelta = transaction.cash / units

        position_new = []
        gains = []

        for lot in position:
            if lot in affected:
                netprice = lot.price - priceDelta
                if netprice < 0:
                    gains.append(Gain(lot=lot, transaction=transaction,
                                      price=priceDelta))
                    netprice = 0
                position_new.append(lot._replace(price=netprice))
            else:
                position_new.append(lot)

        self[pocket] = position_new

        return gains

    def split(self, transaction, sort=None):
        """
        Increase/decrease Lot units without affecting basis or realizing Gain.
        """
        self._validate_args(transaction, numerator=Decimal,
                            denominator=Decimal, units=Decimal)

        splitRatio = transaction.numerator / transaction.denominator

        pocket = (transaction.fiaccount, transaction.security)
        position = self[pocket]

        criterion = openAsOf(transaction.datetime)
        position_new = []
        unitsTo = Decimal('0')
        unitsFrom = Decimal('0')

        for lot in position:
            if criterion(lot):
                units = lot.units * splitRatio
                price = lot.price / splitRatio
                position_new.append(lot._replace(units=units, price=price))
                unitsFrom += lot.units
                unitsTo += units
            else:
                position_new.append(lot)

        calcUnits = unitsTo - unitsFrom
        if abs(calcUnits - transaction.units) > Decimal('0.001'):
            msg = (f"For Lot.unitsFrom={unitsFrom}, split ratio "
                   f"{transaction.numerator}:{transaction.denominator} should yield "
                   f"units={calcUnits} not units={transaction.units}")
            raise Inconsistent(transaction, msg)

        self[pocket] = position_new

        # Stock splits don't realize Gains
        return []

    def transfer(self, transaction, sort=None):
        """
        Move Lots from one Position to another, maybe changing Security/units.
        """
        self._validate_args(transaction, units=Decimal, unitsFrom=Decimal)
        if transaction.units * transaction.unitsFrom >= 0:
            msg = f"units and unitsFrom aren't oppositely signed in {transaction}"
            raise ValueError(msg)

        ratio = -transaction.units / transaction.unitsFrom
        pocketFrom = (transaction.fiaccountFrom, transaction.securityFrom)
        positionFrom = self[pocketFrom]
        if not positionFrom:
            msg = f"No position in {pocketFrom}"
            raise Inconsistent(transaction, msg)
        sort = sort or FIFO
        positionFrom.sort(**sort)

        # Remove the Lots from the source Position
        try:
            lotsFrom, positionFrom = take_lots(positionFrom,
                                               openAsOf(transaction.datetime),
                                               -transaction.unitsFrom)
        except Inconsistent as err:
            raise Inconsistent(transaction, err.msg)

        lunitsFrom = sum([l.units for l in lotsFrom])
        tunitsFrom = transaction.unitsFrom
        if abs(lunitsFrom + tunitsFrom) > 0.001:
            msg = (f"Position in {pocketFrom} has units={lunitsFrom}; "
                   f"can't satisfy unitsFrom={tunitsFrom}")
            raise Inconsistent(transaction, msg)

        self[pocketFrom] = positionFrom

        # Transform Lots to the destination Security/units and apply
        # as a Trade (to order closed Lots, if any) with opentxid & opendt
        # preserved from the source Lot
        gains = []
        for lotFrom in lotsFrom:
            units = lotFrom.units * ratio
            # FIXME - We need a Trade.id for self.trade() to set
            # Lot.createtxid, but "id=transaction.id" is problematic.
            trade = Transaction(
                id=transaction.id,
                uniqueid=transaction.uniqueid,
                datetime=transaction.datetime,
                type='transfer',
                memo=transaction.memo,
                currency=lotFrom.currency,
                cash=-lotFrom.price * lotFrom.units,
                fiaccount=transaction.fiaccount,
                security=transaction.security,
                units=units
            )
            gs = self.trade(trade, opentransaction=lotFrom.opentransaction,
                            createtransaction=transaction)
            gains.extend(gs)

        return gains

    def spinoff(self, transaction, sort=None):
        """
        Remove cost from Position to create Lots in a new Security, preserving
        the holding period through the spinoff and not removing units or
        closing Lots from the source Position.
        """
        self._validate_args(transaction,
                            units=Decimal, numerator=Decimal,
                            denominator=Decimal,
                            securityPrice=(type(None), Decimal),
                            securityFromPrice=(type(None), Decimal))

        units = transaction.units
        securityFrom = transaction.securityFrom
        numerator = transaction.numerator
        denominator = transaction.denominator
        securityPrice = transaction.securityPrice
        securityFromPrice = transaction.securityFromPrice

        pocketFrom = (transaction.fiaccount, securityFrom)
        positionFrom = self[pocketFrom]

        splitRatio = numerator / denominator

        costFraction = 0
        if (securityPrice is not None) and (securityFromPrice is not None):
            costFraction = Decimal(securityPrice * units) / (
                Decimal(securityPrice * units)
                + securityFromPrice * units / splitRatio)

        # Take the basis from the source Position
        lotsFrom, positionFrom = take_basis(positionFrom,
                                            openAsOf(transaction.datetime),
                                            costFraction)

        takenUnits = sum([lot.units for lot in lotsFrom])
        if abs(takenUnits * splitRatio - units) > 0.0001:
            msg = (f"Spinoff {numerator} for {denominator} requires {securityFrom} "
                   f"units={units / splitRation} (not units={takenUnits}) "
                   f"to yield {transactions.security} units={units}")
            raise Inconsistent(transaction, msg)

        self[pocketFrom] = positionFrom

        # Transform Lots to the destination Security/units and apply
        # as a Trade (to order closed Lots, if any) with opentxid & opendt
        # preserved from the source Lot
        gains = []
        for lotFrom in lotsFrom:
            units = lotFrom.units * splitRatio
            # FIXME - We need a Trade.id for self.trade() to set
            # Lot.createtxid, but "id=transaction.id" is problematic.
            trade = Transaction(
                id=transaction.id,
                uniqueid=transaction.uniqueid,
                datetime=transaction.datetime,
                type='trade',
                memo=transaction.memo,
                currency=lotFrom.currency,
                cash=-lotFrom.price * lotFrom.units,
                fiaccount=transaction.fiaccount,
                security=transaction.security,
                units=units
            )
            gs = self.trade(trade, opentransaction=lotFrom.opentransaction,
                            createtransaction=transaction, sort=sort)
            gains.extend(gs)

        return gains

    def exercise(self, transaction, sort=None):
        """
        Options exercise
        """
        self._validate_args(transaction, unitsFrom=Decimal, cash=Decimal)

        unitsFrom = transaction.unitsFrom
        cash = transaction.cash

        pocketFrom = (transaction.fiaccount, transaction.securityFrom)
        positionFrom = self[pocketFrom]

        # Remove lots from the source Position
        try:
            lotsFrom, positionFrom = take_lots(positionFrom,
                                               openAsOf(transaction.datetime),
                                               -unitsFrom)
        except Inconsistent as err:
            raise Inconsistent(transaction, err.msg)

        takenUnits = sum([lot.units for lot in lotsFrom])
        if abs(takenUnits) - abs(unitsFrom) > 0.0001:
            msg = f"Exercise Lot.units={takenUnits} (not {unitsFrom})"
            raise Inconsistent(transaction, msg)

        self[pocketFrom] = positionFrom

        multiplier = abs(transaction.units / unitsFrom)

        # Transform Lots to the destination Security/units, add additional
        # exercise cash as cost pro rata, and apply as a Trade (to order
        # closed Lots, if any)
        gains = []
        for lotFrom in lotsFrom:
            adjusted_price = -lotFrom.price * lotFrom.units \
                    + cash * lotFrom.units / takenUnits
            currency = lotFrom.currency

            units = lotFrom.units * multiplier
            # FIXME - We need a Trade.id for self.trade() to set
            # Lot.createtxid, but "id=transaction.id" is problematic.
            trade = Transaction(
                type='trade', id=transaction.id,
                fiaccount=transaction.fiaccount, uniqueid=transaction.uniqueid,
                datetime=transaction.datetime, memo=transaction.memo,
                security=transaction.security, units=units,
                cash=adjusted_price, currency=currency)
            gs = self.trade(trade, sort=sort)
            gains.extend(gs)

        return gains

    @staticmethod
    def _validate_args(transaction, **kwargs):
        for arg, val in kwargs.items():
            attr = getattr(transaction, arg)
            if not isinstance(attr, val):
                # Unpack kwarg value sequences
                if hasattr(val, '__getitem__'):
                    val = tuple(v.__name__ for v in val)
                else:
                    val = val.__name__
                attrname = f"{transaction.__class.__.__name__}.{arg}"
                msg = (f"{attrname} must be type {val}, "
                       f"not {type(attr).__name__}: {transaction}")
                raise ValueError(msg)

    def processTransaction(self, transaction, sort=None):
        sort = sort or globals().get(transaction.sort, None)
        handler = getattr(self, transaction.type)
        gains = handler(transaction, sort=sort)
        return gains


###############################################################################
# REPORTING FUNCTIONS
###############################################################################
# Data container for reporting gain
GainReport = namedtuple('GainReport',
                        ['fiaccount', 'security', 'opentx', 'gaintx', 'units',
                         'currency', 'cost', 'proceeds', 'longterm'])


def report_gain(session, gain):
    """
    Crunch the numbers for a Gain instance.

    Returns a GainReport instance.
    """
    gain = translate_gain(session, gain)

    gaintx = gain.transaction
    fiaccount = gaintx.fiaccount
    security = gaintx.security

    lot = gain.lot
    opentx = lot.opentransaction

    units = lot.units
    proceeds = units * gain.price
    cost = units * lot.price
    gaindt = gain.transaction.datetime
    opendt = lot.opentransaction.datetime
    longterm = (units > 0) and (gaindt - opendt >= timedelta(days=366))

    return GainReport(fiaccount=fiaccount, security=security, opentx=opentx,
                      gaintx=gaintx, units=units, currency=lot.currency,
                      cost=cost, proceeds=proceeds, longterm=longterm)


def translate_gain(session, gain):
    """
    Translate Gain instance's realizing transaction to functional currency.

    Returns a Gain instance.
    """
    # 26 CFR §1.988-2(a)(2)(iv)
    # (A)Amount realized. If stock or securities traded on an established
    # securities market are sold by a cash basis taxpayer for nonfunctional
    # currency, the amount realized with respect to the stock or securities
    # (as determined on the trade date) shall be computed by translating
    # the units of nonfunctional currency received into functional currency
    # at the spot rate on the _settlement date_ of the sale.  [...]
    #
    # (B)Basis. If stock or securities traded on an established securities
    # market are purchased by a cash basis taxpayer for nonfunctional
    # currency, the basis of the stock or securities shall be determined
    # by translating the units of nonfunctional currency paid into
    # functional currency at the spot rate on the _settlement date_ of the
    # purchase.
    lot, gaintx, gainprice = gain.lot, gain.transaction, gain.price

    functional_currency = CONFIG['books']['functional_currency']

    assert lot.currency
    if lot.currency != functional_currency:
        opentx = lot.opentransaction
        dtsettle = opentx.dtsettle or opentx.datetime
        date_settle = date(dtsettle.year, dtsettle.month, dtsettle.day)
        exchange_rate = CurrencyRate.get_rate(
            session, fromcurrency=lot.currency, tocurrency=functional_currency,
            date=date_settle)
        opentx_translated = translate_transaction(
            opentx, functional_currency, exchange_rate)
        lot = lot._replace(opentransaction=opentx_translated,
                           price=lot.price * exchange_rate,
                           currency=functional_currency)

    gaintx_currency = gaintx.currency or lot.currency
    assert gaintx_currency
    if gaintx_currency != functional_currency:
        dtsettle = gaintx.dtsettle or gaintx.datetime
        date_settle = date(dtsettle.year, dtsettle.month, dtsettle.day)
        exchange_rate = CurrencyRate.get_rate(
            session, fromcurrency=gaintx_currency,
            tocurrency=functional_currency, date=date_settle)

        gaintx = translate_transaction(gaintx,
                                       functional_currency, exchange_rate)
        gainprice = gainprice * exchange_rate

    return Gain(lot, gaintx, gainprice)


def translate_transaction(transaction, currency, rate):
    securityPrice = transaction.securityPrice
    if securityPrice is not None:
        securityPrice = transaction.securityPrice * rate,

    securityFromPrice = transaction.securityFromPrice
    if securityFromPrice is not None:
        securityFromPrice = transaction.securityFromPrice * rate,

    return Transaction(
        id=transaction.id, uniqueid=transaction.uniqueid,
        datetime=transaction.datetime, dtsettle=transaction.dtsettle,
        type=transaction.type, memo=transaction.memo, currency=currency,
        cash=transaction.cash * rate, fiaccount=transaction.fiaccount,
        security=transaction.security, units=transaction.units,
        securityPrice=securityPrice,
        fiaccountFrom=transaction.fiaccountFrom,
        securityFrom=transaction.securityFrom, unitsFrom=transaction.unitsFrom,
        securityFromPrice=securityFromPrice,
        numerator=transaction.numerator, denominator=transaction.denominator,
        sort=transaction.sort)


###############################################################################
# FILTER CRITERIA
###############################################################################
def openAsOf(datetime_):
    """
    Filter function that chooses Lots created on or before datetime
    """
    def isOpen(lot):
        return lot.createtransaction.datetime <= datetime_

    return isOpen


def longAsOf(datetime_):
    """
    Filter function that chooses long Lots (i.e. positive units) created
    on or before datetime
    """
    def isOpen(lot):
        lot_open = lot.createtransaction.datetime <= datetime_
        lot_long = lot.units > 0
        return lot_open and lot_long

    return isOpen


def closableBy(transaction):
    """
    Filter function that chooses Lots created on or before the given
    transaction.datetime, with sign opposite to the given transaction.units
    """
    def closeMe(lot):
        lot_open = lot.createtransaction.datetime <= transaction.datetime
        opposite_sign = lot.units * transaction.units < 0
        return lot_open and opposite_sign

    return closeMe


###############################################################################
# SORT FUNCTIONS
###############################################################################
def sort_oldest(lot):
    """
    Sort by holding period, then by opening Transaction.uniqueid
    """
    opendt = lot.opentransaction.datetime
    opentxid = lot.opentransaction.uniqueid
    assert opendt is not None
    return (str(opendt), opentxid or '')


def sort_cheapest(lot):
    """
    Sort by price, then by opening Transaction.uniqueid
    """
    # FIXME this doesn't sort stably for identical prices but different lots
    price = lot.price
    opentxid = lot.opentransaction.uniqueid
    assert price is not None
    return (price, opentxid or '')


def sort_dearest(lot):
    """
    Sort by price, then by opening Transaction.uniqueid
    """
    # FIXME this doesn't sort stably for identical prices but different lots
    price = lot.price
    opentxid = lot.opentransaction.uniqueid
    assert price is not None
    return (-price, opentxid or '')


FIFO = {'key': sort_oldest, 'reverse': False}
LIFO = {'key': sort_oldest, 'reverse': True}
MINGAIN = {'key': sort_dearest, 'reverse': False}
MAXGAIN = {'key': sort_cheapest, 'reverse': False}
