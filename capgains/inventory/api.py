# coding: utf-8
"""Functions to apply securities transactions to inventory and compute realized gains.

Besides the fundamental requirement of keeping accurate tallies, the main purpose
of this module is to match opening and closing transactions in order to calculate
the amount and character of realized gains.

To use this module, create a Portfolio instance and call its book() method, passing in
instances of type capgains.inventory.models.TransactionType.  Alternatively, you can use
any object that implements the mapping protocol, and pass it to the module-level book()
function.

The functions in this module are impure; they mutate the input Portfolio (a collection
of Lots) as a side effect and return Gains. Gains refer to Lots, which are immutable;
changes to a Lot are reflected in a newly-created Lot, leaving the old Lot undisturbed
to preserve referential integrity. A gain.lot refers to the portfolio state at the
moment of the realizing transaction, not the current state.

Gains also refer to transactions, which generally are models.Transaction instances
(wrapping DB rows) are mutable.  You can harm referential integrity by mutating
Transactions after you have bound them to Gains.  Don't to that.  Nothing in this
module mutates a Transaction, once created.

We could plug this hole by converting each models.Transaction to an immutable
inventory.types.DummyTransaction, and converting each FiAccount/Security to an immutable
dummy version, but we'd prefer not to.  It's handy for Lots and Gains to have "live"
references to SQLAlchemy wrappers for Transactions/FiAccounts/Securities during
interactive interpreter sessions.

To compute realized capital gains from a Gain instance:
    * Proceeds = gain.lot.units * gain.price
    * Basis = gain.lot.units * gain.lot.price
    * Holding period start = gain.lot.opentransaction.datetime
    * Holding period end = gain.transaction.datetime
"""

__all__ = [
    "Inconsistent",
    "UNITS_TOLERANCE",
    "Portfolio",
    "book",
    "book_model",
    "book_trade",
    "book_returnofcapital",
    "book_split",
    "book_transfer",
    "book_spinoff",
    "book_transfer",
]


# stdlib imports
from collections import defaultdict
from decimal import Decimal
import itertools
import functools
from typing import Tuple, List, MutableMapping, Any, Optional, Union


# local imports
from capgains import models, utils
from capgains.inventory import functions
from .types import (
    Lot,
    Gain,
    TransactionType,
    Trade,
    ReturnOfCapital,
    Transfer,
    Split,
    Spinoff,
    Exercise,
)
from .predicates import openAsOf, longAsOf, closable
from .sortkeys import SortType, FIFO


class InventoryError(Exception):
    """ Base class for Exceptions defined in this module """


class Inconsistent(InventoryError):
    """Exception raised when a Position's state is inconsistent with Transaction.

    Args:
        transaction: the transaction instance that couldn't be applied.
        msg: Error message detailing the inconsistency.

    Attributes:
        transaction: the transaction instance that couldn't be applied.
        msg: Error message detailing the inconsistency.
    """

    def __init__(self, transaction: "TransactionType", msg: str) -> None:
        self.transaction = transaction
        self.msg = msg
        super(Inconsistent, self).__init__(f"{transaction} inconsistent: {msg}")


UNITS_TOLERANCE = Decimal("0.001")
"""Significance threshold for difference between predicted units and reported units.

For transactions that involve scaling units by a ratio (i.e. Split & Spinoff), if the
product of that ratio and the total position Lot.units affected by the transaction
differs from the reported transaction.units/fromunits by more than UNITS_TOLERANCE, then
an Inconsistent error is raised.
"""


class Portfolio(defaultdict):
    """Mapping container for securities positions (i.e. lists of Lot instances).

    Keyed by (FI account, security) a/k/a "pocket".

    Note:
        Any object implementing the mapping protocol may be used with the functions in
        this module.  It's convenient to inherit from collections.defaultdict.
    """

    default_factory = list

    def __init__(self, *args, **kwargs):
        args = (self.default_factory,) + args
        defaultdict.__init__(self, *args, **kwargs)

    def book(
        self, transaction: TransactionType, sort: Optional[SortType] = None
    ) -> List[Gain]:
        """Convenience method to call inventory.book()

        Args:
            transaction: the transaction to apply to the Portfolio.
            sort: sort algorithm for gain recognition.

        Returns:
            A sequence of Gain instances, reflecting Lots closed by the transaction.
        """
        return book(transaction, self, sort=sort)


FiAccount = Any
Security = Any
PortfolioType = MutableMapping[Tuple[FiAccount, Security], List[Lot]]


@functools.singledispatch
def book(transaction, *args, **kwargs) -> List[Gain]:
    """Apply a Transaction to the appropriate position(s) in the Portfolio.

    Dispatch to handler function below based on type of transaction.

    Raises:
        ValueError: if functools.singledispatch doesn't have a handler registered
                    for the transaction type.
    """

    raise ValueError(f"Unknown transaction type {type(transaction)}")


@book.register
def book_model(
    transaction: models.Transaction,
    portfolio: PortfolioType,
    *,
    sort: Optional[SortType] = None,
) -> List[Gain]:
    """Apply a models.Transaction to the appropriate position(s) in the Portfolio.

    models.Transaction doesn't have subclasses, so dispatch based on the instance's
    type attribute.

    Args:
        transaction: the transaction to apply to the Portfolio.
        portfolio: map of (FI account, security) to list of Lots.
        sort: sort algorithm for gain recognition e.g. FIFO, used to order closed Lots.

    Returns:
        A sequence of Gain instances, reflecting Lots closed by the transaction.
    """

    handlers = {
        models.TransactionType.TRADE: book_trade,
        models.TransactionType.RETURNCAP: book_returnofcapital,
        models.TransactionType.SPLIT: book_split,
        models.TransactionType.TRANSFER: book_transfer,
        models.TransactionType.SPINOFF: book_spinoff,
        models.TransactionType.EXERCISE: book_exercise,
    }
    handler = handlers[transaction.type]
    gains = handler(transaction, portfolio, sort=sort)  # type: ignore
    return gains


@book.register(Trade)
def book_trade(
    transaction: Union[Trade, models.Transaction],
    portfolio: PortfolioType,
    *,
    sort: Optional[SortType] = None,
) -> List[Gain]:
    """Apply a Trade to the appropriate position(s) in the Portfolio.

    Args:
        transaction: the transaction to apply to the Portfolio.
        portfolio: map of (FI account, security) to list of Lots.
        sort: sort algorithm for gain recognition e.g. FIFO, used to order closed Lots.

    Returns:
        A sequence of Gain instances, reflecting Lots closed by the transaction.

    Raises:
        ValueError: if `Trade.units` is zero.
    """
    if transaction.units == 0:
        raise ValueError(f"units can't be zero: {transaction}")

    return _mutate_portfolio(
        portfolio=portfolio,
        transaction=transaction,
        units=transaction.units,
        cash=transaction.cash,
        currency=transaction.currency,
        sort=sort,
    )


@book.register(ReturnOfCapital)
def book_returnofcapital(
    transaction: Union[ReturnOfCapital, models.Transaction],
    portfolio: PortfolioType,
    **_,
) -> List[Gain]:
    """Apply a ReturnOfCapital to the appropriate position(s) in the Portfolio.

    Note:
        Sort algorithm is irrelevant for ReturnOfCapital, which closes no Lots.

    Args:
        transaction: the transaction to apply to the Portfolio.
        portfolio: map of (FI account, security) to list of Lots.

    Returns:
        A sequence of Gain instances, reflecting Lots closed by the transaction.

    Raises:
        Inconsistent: if no position in the `portfolio` as of `ReturnOfCapital.datetime`
                      is found to receive the distribution.
    """
    pocket = (transaction.fiaccount, transaction.security)
    position = portfolio.get(pocket, [])

    # First get a total of shares affected by return of capital,
    # in order to determine return of capital per share
    unaffected, affected = utils.partition(longAsOf(transaction.datetime), position)
    affected = list(affected)
    if not affected:
        msg = (
            f"Return of capital {transaction}:\n"
            f"FI account {transaction.fiaccount} has no long position in "
            f"{transaction.security} as of {transaction.datetime}"
        )
        raise Inconsistent(transaction, msg)

    unitROC = transaction.cash / sum([lot.units for lot in affected])

    def reduceBasis(lot: Lot, unitROC: Decimal) -> Tuple[Lot, Optional[Gain]]:
        gain = None
        newBasis = lot.price - unitROC
        if newBasis < 0:
            gain = Gain(lot=lot, transaction=transaction, price=unitROC)
            newBasis = Decimal("0")
        return (lot._replace(price=newBasis), gain)

    basisReduced, gains = zip(*(reduceBasis(lot, unitROC) for lot in affected))
    portfolio[pocket] = list(basisReduced) + list(unaffected)
    return [gain for gain in gains if gain is not None]


@book.register(Split)
def book_split(
    transaction: Union[Split, models.Transaction], portfolio: PortfolioType, **_
) -> List[Gain]:
    """Apply a Split to the appropriate position(s) in the Portfolio.

    Note:
        Sort algorithm is irrelevant for Splits, which close no Lots.

    Args:
        transaction: the transaction to apply to the Portfolio.
        portfolio: map of (FI account, security) to list of Lots.

    Returns:
        A sequence of Gain instances, reflecting Lots closed by the transaction.

    Raises:
        Inconsistent: if the relevant position in the `portfolio`, when adjusted for
                      the split ratio, wouldn't cause a share delta that matches
                      `Split.units`.
    """
    splitRatio = transaction.numerator / transaction.denominator

    pocket = (transaction.fiaccount, transaction.security)
    position = portfolio.get(pocket, [])

    if not position:
        msg = (
            f"Split {transaction.security} "
            f"{transaction.numerator}:{transaction.denominator} "
            f"on {transaction.datetime} -\n"
            f"No position in FI account {transaction.fiaccount}"
        )
        raise Inconsistent(transaction, msg)

    unaffected, affected = utils.partition(openAsOf(transaction.datetime), position)

    def _split(lot: Lot, ratio: Decimal) -> Tuple[Lot, Decimal]:
        """ Returns (post-split Lot, original Units) """
        units = lot.units * ratio
        price = lot.price / ratio
        return (lot._replace(units=units, price=price), lot.units)

    position_new, origUnits = zip(*(_split(lot, splitRatio) for lot in affected))
    newUnits = sum([lot.units for lot in position_new]) - sum(origUnits)
    if abs(newUnits - transaction.units) > UNITS_TOLERANCE:
        msg = (
            f"Split {transaction.security} "
            f"{transaction.numerator}:{transaction.denominator} -\n"
            f"To receive {transaction.units} units {transaction.security} "
            f"requires a position of {transaction.units / splitRatio} units of "
            f"{transaction.security} in FI account {transaction.fiaccount} "
            f"on {transaction.datetime}, not units={origUnits}"
        )
        raise Inconsistent(transaction, msg)

    portfolio[pocket] = list(position_new) + list(unaffected)

    # Stock splits don't realize Gains
    return []


@book.register(Transfer)
def book_transfer(
    transaction: Union[Transfer, models.Transaction],
    portfolio: PortfolioType,
    *,
    sort: Optional[SortType] = None,
) -> List[Gain]:
    """Apply a Transfer to the appropriate position(s) in the Portfolio.

    Args:
        transaction: the transaction to apply to the Portfolio.
        portfolio: map of (FI account, security) to list of Lots.
        sort: sort algorithm for gain recognition e.g. FIFO, used to order closed Lots.

    Returns:
        A sequence of Gain instances, reflecting Lots closed by the transaction.

    Raises:
        ValueError: if `Transfer.units` and `Transfer.fromunits` aren't
                    oppositely signed.
        Inconsistent: if the relevant position in `portfolio` is insufficient to
                      satisfy `Transfer.fromunits`.
    """

    if transaction.units * transaction.fromunits >= 0:
        msg = f"units and fromunits aren't oppositely signed in {transaction}"
        raise ValueError(msg)

    sourcePocket = (transaction.fromfiaccount, transaction.fromsecurity)
    try:
        sourcePosition = portfolio[sourcePocket]
    except KeyError:
        raise Inconsistent(transaction, f"No position in {sourcePocket}")

    lotsRemoved, sourcePosition = functions.part_units(
        position=sourcePosition,
        predicate=openAsOf(transaction.datetime),
        max_units=-transaction.fromunits,
    )

    unitsRemoved = sum([lot.units for lot in lotsRemoved])
    if abs(unitsRemoved + transaction.fromunits) > UNITS_TOLERANCE:
        msg = (
            f"Position in {transaction.security} for FI account "
            f"{transaction.fiaccount} on {transaction.datetime} is only "
            f"{unitsRemoved} units; can't transfer out {transaction.units} units."
        )
        raise Inconsistent(transaction, msg)

    portfolio[sourcePocket] = sourcePosition

    transferRatio = -transaction.units / transaction.fromunits

    gains = (
        _mutate_portfolio(
            portfolio=portfolio,
            transaction=transaction,
            units=lot.units * transferRatio,
            currency=lot.currency,
            cash=-lot.price * lot.units,
            opentransaction=lot.opentransaction,
            sort=sort,
        )
        for lot in lotsRemoved
    )
    return list(itertools.chain.from_iterable(gains))


#  FIXME - account for the sometimes-lengthy gap between `datetime` and `dtsettle`
@book.register(Spinoff)
def book_spinoff(
    transaction: Union[Spinoff, models.Transaction],
    portfolio: PortfolioType,
    *,
    sort: Optional[SortType] = None,
) -> List[Gain]:
    """Apply a Spinoff to the appropriate position(s) in the Portfolio.

    Args:
        transaction: the transaction to apply to the Portfolio.
        portfolio: map of (FI account, security) to list of Lots.
        sort: sort algorithm for gain recognition e.g. FIFO, used to order closed Lots.

    Returns:
        A sequence of Gain instances, reflecting Lots closed by the transaction.

    Raises:
        ValueError: if either `Spinoff.numerator` or `Spinoff.denominator` isn't a
                    positive number.
        Inconsistent: if the relevant position in `portfolio` as of `Spinoff.datetime`,
                      when adjusted for the spinoff ratio, wouldn't produce a change in
                      # units that matches `Spinoff.units`.
    """

    if transaction.numerator <= 0 or transaction.denominator <= 0:
        msg = f"numerator & denominator must be positive Decimals in {transaction}"
        raise ValueError(msg)

    sourcePocket = (transaction.fiaccount, transaction.fromsecurity)
    try:
        sourcePosition = portfolio[sourcePocket]
    except KeyError:
        raise Inconsistent(transaction, f"No position in {sourcePocket}")
    sourcePosition.sort(**(sort or FIFO))

    spinRatio = Decimal(transaction.numerator) / Decimal(transaction.denominator)

    # costFraction is the fraction of original cost allocated to the spinoff,
    # with the balance allocated to the source position.
    if transaction.securityprice is None or transaction.fromsecurityprice is None:
        costFraction = Decimal("0")
    else:
        spinoffFMV = transaction.securityprice * transaction.units
        spunoffFMV = transaction.fromsecurityprice * transaction.units / spinRatio
        costFraction = spinoffFMV / (spinoffFMV + spunoffFMV)

    # Take the basis from the source Position
    lotsRemoved, sourcePosition = functions.part_basis(
        position=sourcePosition,
        predicate=openAsOf(transaction.datetime),
        max_units=costFraction,
    )

    unitsRemoved = sum([lot.units for lot in lotsRemoved])
    if abs(unitsRemoved * spinRatio - transaction.units) > UNITS_TOLERANCE:
        msg = (
            f"Spinoff {transaction.numerator} units {transaction.security} "
            f"for {transaction.denominator} units {transaction.fromsecurity}:\n"
            f"To receive {transaction.units} units {transaction.security} "
            f"requires a position of {transaction.units / spinRatio} units of "
            f"{transaction.fromsecurity} in FI account {transaction.fiaccount} "
            f"on {transaction.datetime}, not units={unitsRemoved}"
        )
        raise Inconsistent(transaction, msg)

    portfolio[sourcePocket] = sourcePosition

    gains = (
        _mutate_portfolio(
            portfolio=portfolio,
            transaction=transaction,
            units=lotFrom.units * spinRatio,
            currency=lotFrom.currency,
            cash=-lotFrom.price * lotFrom.units,
            opentransaction=lotFrom.opentransaction,
            sort=sort,
        )
        for lotFrom in lotsRemoved
    )
    return list(itertools.chain.from_iterable(gains))


@book.register(Exercise)
def book_exercise(
    transaction: Union[Exercise, models.Transaction],
    portfolio: PortfolioType,
    *,
    sort: Optional[SortType] = None,
) -> List[Gain]:
    """Apply an Exercise transaction to the appropriate position(s) in the Portfolio.

    Args:
        transaction: the transaction to apply to the Portfolio.
        portfolio: map of (FI account, security) to list of Lots.
        sort: sort algorithm for gain recognition e.g. FIFO, used to order closed Lots.

    Returns:
        A sequence of Gain instances, reflecting Lots closed by the transaction.

    Raises:
        Inconsistent: if the relevant position in `portfolio` as of `Exercise.datetime`
                      doesn't contain enough units of the option to satisfy the
                      `Exercise.units`.
    """

    fromunits = transaction.fromunits

    sourcePocket = (transaction.fiaccount, transaction.fromsecurity)
    sourcePosition = portfolio.get(sourcePocket, [])

    lotsRemoved, sourcePosition = functions.part_units(
        position=sourcePosition,
        predicate=openAsOf(transaction.datetime),
        max_units=-fromunits,
    )

    unitsRemoved = sum([lot.units for lot in lotsRemoved])
    if abs(unitsRemoved) - abs(fromunits) > UNITS_TOLERANCE:
        msg = f"Exercise Lot.units={unitsRemoved} (not {fromunits})"
        raise Inconsistent(transaction, msg)

    portfolio[sourcePocket] = sourcePosition

    multiplier = abs(transaction.units / transaction.fromunits)
    strikePrice = abs(transaction.cash / transaction.units)

    gains = (
        _mutate_portfolio(
            portfolio=portfolio,
            transaction=transaction,
            units=lot.units * multiplier,
            currency=lot.currency,
            cash=(lot.price * -lot.units) + (lot.units * multiplier * strikePrice),
            sort=sort,
        )
        for lot in lotsRemoved
    )
    return list(itertools.chain.from_iterable(gains))


def _mutate_portfolio(
    portfolio: PortfolioType,
    transaction: TransactionType,
    units: Decimal,
    cash: Decimal,
    currency: models.Currency,
    *,
    opentransaction: Optional[TransactionType] = None,
    sort: Optional[SortType] = None,
) -> List[Gain]:
    """Apply a transaction's units to a Portfolio, opening/closing Lots as appropriate.

    The Portfolio is modified in place as a side effect; return vals are realized Gains.

    Note:
        Transactions which transform basis (Transfer, Spinoff, Exercise) must first take
        basis from the "source pocket", i.e. (fromfiaccount, fromsecurity, fromunits)
        before calling this function to apply the removed basis to the transaction's
        "destination pocket", i.e. (account, security, units).

    Args:
        portfolio: map of (FI account, security) to list of Lots.
        transaction: the source transaction generating the units.
        units: amount of security to add to/subtract from position.
        cash: money amount (basis/proceeds) attributable to the units.
        currency: currency denomination of basis/proceeds
        opentransaction: opening transaction of record (establishing holding period)
                         for any Lots created by applying the transaction.  By default,
                         use the current transaction being processed.
        sort: sort algorithm for gain recognition e.g. FIFO, used to order closed Lots.

    Returns:
        A sequence of Gain instances, reflecting Lots closed by the transaction.
    """
    pocket = (transaction.fiaccount, transaction.security)
    position = portfolio.get(pocket, [])
    position.sort(**(sort or FIFO))

    price = abs(cash / units)

    # First remove existing Position Lots closed by the transaction.
    lotsClosed, position = functions.part_units(
        postion=position,
        predicate=closable(units, transaction.datetime),
        max_units=-units,
    )

    # Units not consumed in closing existing Lots are applied as basis in a new Lot.
    units += sum([lot.units for lot in lotsClosed])
    if units != 0:
        newLot = Lot(
            opentransaction=opentransaction or transaction,
            createtransaction=transaction,
            units=units,
            price=price,
            currency=currency,
        )
        position.append(newLot)

    portfolio[pocket] = position

    # Bind closed Lots to realizing transaction to generate Gains.
    return [Gain(lot=lot, transaction=transaction, price=price) for lot in lotsClosed]
