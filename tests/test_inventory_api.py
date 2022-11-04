# coding: utf-8
"""
"""
# stdlib imports
import unittest
from decimal import Decimal
from datetime import datetime


# local imports
from tradingdiary.inventory import (
    FIFO,
    LIFO,
    MINGAIN,
    MAXGAIN,
    Lot,
    Gain,
    Portfolio,
    Trade,
    ReturnOfCapital,
    Split,
    Transfer,
    Spinoff,
    #  Exercise,
    Inconsistent,
    part_units,
    part_basis,
    openAsOf,
)


class TradeTestCase(unittest.TestCase):
    def setUp(self):
        self.trades = [
            Trade(
                uniqueid="20160104.U99.e.USD.1468544894",
                datetime=datetime(2016, 1, 4, 14, 57, 40),
                fiaccount=None,
                security=None,
                units=Decimal("-200.00"),
                # price=Decimal('15.808'),
                cash=Decimal("3161.5975047"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160104.U99.e.USD.1468552856",
                datetime=datetime(2016, 1, 4, 14, 59, 51),
                fiaccount=None,
                security=None,
                units=Decimal("-300.00"),
                # price=Decimal('15.7979'),
                cash=Decimal("4739.36631225"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160104.U99.e.USD.1468552920",
                datetime=datetime(2016, 1, 4, 14, 59, 53),
                fiaccount=None,
                security=None,
                units=Decimal("-300.00"),
                # price=Decimal('15.7973'),
                cash=Decimal("4739.18631225"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160104.U99.e.USD.1468942125",
                datetime=datetime(2016, 1, 4, 17, 33, 15),
                fiaccount=None,
                security=None,
                units=Decimal("-200.00"),
                # price=Decimal('15.7973'),
                cash=Decimal("3159.4575415"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160105.U99.e.USD.1469598029",
                datetime=datetime(2016, 1, 5, 14, 49, 36),
                fiaccount=None,
                security=None,
                units=Decimal("-100.00"),
                # price=Decimal('16.9129'),
                cash=Decimal("1691.28670995"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160105.U99.e.USD.1469598030",
                datetime=datetime(2016, 1, 5, 14, 49, 36),
                fiaccount=None,
                security=None,
                units=Decimal("-100.00"),
                # price=Decimal('16.908'),
                cash=Decimal("1690.79672835"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160105.U99.e.USD.1469598191",
                datetime=datetime(2016, 1, 5, 14, 49, 36),
                fiaccount=None,
                security=None,
                units=Decimal("-100.00"),
                # price=Decimal('16.9429'),
                cash=Decimal("1694.28665475"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160105.U99.e.USD.1469598198",
                datetime=datetime(2016, 1, 5, 14, 49, 36),
                fiaccount=None,
                security=None,
                units=Decimal("-100.00"),
                # price=Decimal('16.908'),
                cash=Decimal("1690.79672835"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160105.U99.e.USD.1469598231",
                datetime=datetime(2016, 1, 5, 14, 49, 39),
                fiaccount=None,
                security=None,
                units=Decimal("-100.00"),
                # price=Decimal('16.908'),
                cash=Decimal("1690.79672835"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160105.U99.e.USD.1469598296",
                datetime=datetime(2016, 1, 5, 14, 49, 39),
                fiaccount=None,
                security=None,
                units=Decimal("-300.00"),
                # price=Decimal('16.90796666666666666666666667'),
                cash=Decimal("5072.39018505"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160105.U99.e.USD.1469598410",
                datetime=datetime(2016, 1, 5, 14, 49, 42),
                fiaccount=None,
                security=None,
                units=Decimal("-100.00"),
                # price=Decimal('16.908'),
                cash=Decimal("1690.79672835"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160105.U99.e.USD.1469598426",
                datetime=datetime(2016, 1, 5, 14, 49, 43),
                fiaccount=None,
                security=None,
                units=Decimal("-100.00"),
                # price=Decimal('16.908'),
                cash=Decimal("1690.79672835"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160105.U99.e.USD.1469770926",
                datetime=datetime(2016, 1, 5, 15, 58, 28),
                fiaccount=None,
                security=None,
                units=Decimal("-125.00"),
                # price=Decimal('17.50792'),
                cash=Decimal("2188.494530438"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160105.U99.e.USD.1469801076",
                datetime=datetime(2016, 1, 5, 16, 14, 53),
                fiaccount=None,
                security=None,
                units=Decimal("-61.00"),
                # price=Decimal('17.49721311475409836065573770'),
                cash=Decimal("1067.332642078"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160105.U99.e.USD.1469807788",
                datetime=datetime(2016, 1, 5, 16, 18, 29),
                fiaccount=None,
                security=None,
                units=Decimal("-814.00"),
                # price=Decimal('17.49726044226044226044226044'),
                cash=Decimal("14242.766731985"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160113.U99.e.USD.1476575799",
                datetime=datetime(2016, 1, 13, 14, 41, 14),
                fiaccount=None,
                security=None,
                units=Decimal("-1.00"),
                # price=Decimal('14.66'),
                cash=Decimal("14.661247566"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160113.U99.e.USD.1476579053",
                datetime=datetime(2016, 1, 13, 14, 42, 15),
                fiaccount=None,
                security=None,
                units=Decimal("-493.00"),
                # price=Decimal('14.67791075050709939148073022'),
                cash=Decimal("7236.208799542"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160113.U99.e.USD.1476579068",
                datetime=datetime(2016, 1, 13, 14, 42, 15),
                fiaccount=None,
                security=None,
                units=Decimal("-100.00"),
                # price=Decimal('14.7329'),
                cash=Decimal("1473.29072115"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160113.U99.e.USD.1476579070",
                datetime=datetime(2016, 1, 13, 14, 42, 15),
                fiaccount=None,
                security=None,
                units=Decimal("-200.00"),
                # price=Decimal('14.6779'),
                cash=Decimal("2935.5816631"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160113.U99.e.USD.1476581751",
                datetime=datetime(2016, 1, 13, 14, 42, 58),
                fiaccount=None,
                security=None,
                units=Decimal("-200.00"),
                # price=Decimal('14.8529'),
                cash=Decimal("2970.5810007"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160113.U99.e.USD.1476581755",
                datetime=datetime(2016, 1, 13, 14, 42, 58),
                fiaccount=None,
                security=None,
                units=Decimal("-6.00"),
                # price=Decimal('14.8080059235'),
                cash=Decimal("88.848035541"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160113.U99.e.USD.1476581819",
                datetime=datetime(2016, 1, 13, 14, 42, 58),
                fiaccount=None,
                security=None,
                units=Decimal("-1000.00"),
                # price=Decimal('14.8080059235'),
                cash=Decimal("14808.0059235"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160126.U99.e.USD.1487338567",
                datetime=datetime(2016, 1, 26, 17, 52, 17),
                fiaccount=None,
                security=None,
                units=Decimal("258.00"),
                # price=Decimal('10.74170542635658914728682171'),
                cash=Decimal("-2771.359263705"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160126.U99.e.USD.1487338568",
                datetime=datetime(2016, 1, 26, 17, 52, 17),
                fiaccount=None,
                security=None,
                units=Decimal("200.00"),
                # price=Decimal('10.7417'),
                cash=Decimal("-2148.3405145"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160126.U99.e.USD.1487338788",
                datetime=datetime(2016, 1, 26, 17, 52, 25),
                fiaccount=None,
                security=None,
                units=Decimal("200.00"),
                # price=Decimal('10.7417'),
                cash=Decimal("-2148.3405145"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160126.U99.e.USD.1487346935",
                datetime=datetime(2016, 1, 26, 17, 58, 18),
                fiaccount=None,
                security=None,
                units=Decimal("100.00"),
                # price=Decimal('10.7417'),
                cash=Decimal("-1074.17025725"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160126.U99.e.USD.1487346940",
                datetime=datetime(2016, 1, 26, 17, 58, 18),
                fiaccount=None,
                security=None,
                units=Decimal("242.00"),
                # price=Decimal('10.74169421487603305785123967'),
                cash=Decimal("-2599.492022545"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160126.U99.e.USD.1487504352",
                datetime=datetime(2016, 1, 26, 19, 45, 40),
                fiaccount=None,
                security=None,
                units=Decimal("70.00"),
                # price=Decimal('10.74314285714285714285714286'),
                cash=Decimal("-752.02425725"),
                currency="USD",
            ),
            Trade(
                uniqueid="20160126.U99.e.USD.1487510413",
                datetime=datetime(2016, 1, 26, 19, 50, 19),
                fiaccount=None,
                security=None,
                units=Decimal("100.00"),
                # price=Decimal('10.7413'),
                cash=Decimal("-1074.125180075"),
                currency="USD",
            ),
        ]

    def testFifoTrade(self):
        """
        Test FIFO on a series of trades, some with same datetime/different IDs.
        """
        # The first 5 trades are completely closed by the last 7 trades.
        # The 6th trade has 70 of 100 units closed by the last trade.
        matchedTrades = [
            (0, 22, Decimal("-200")),
            (1, 22, Decimal("-58")),
            (1, 23, Decimal("-200")),
            (1, 24, Decimal("-42")),
            (2, 24, Decimal("-158")),
            (2, 25, Decimal("-100")),
            (2, 26, Decimal("-42")),
            (3, 26, Decimal("-200")),
            (4, 27, Decimal("-70")),
            (4, 28, Decimal("-30")),
            (5, 28, Decimal("-70")),
        ]
        partial = (5, Decimal("-30"))
        self._testTradeSort(FIFO, matchedTrades, partial)

    def testLifoTrade(self):
        """
        Test LIFO on a series of trades, some with same datetime/different IDs.
        """
        # Trades 20 & 21 are completely closed by trades 22-26.
        # Trade 19 has 164 of 200 units closed by trades 27-28.
        matchedTrades = [
            (19, 27, Decimal("-64")),
            (19, 28, Decimal("-100")),
            (20, 27, Decimal("-6")),
            (21, 22, Decimal("-258")),
            (21, 23, Decimal("-200")),
            (21, 24, Decimal("-200")),
            (21, 25, Decimal("-100")),
            (21, 26, Decimal("-242")),
        ]
        partial = (19, Decimal("-36"))
        self._testTradeSort(LIFO, matchedTrades, partial)

    def testMinGainTrade(self):
        """
        Test MINGAIN on a series of trades
        """
        # Trades 12-14 and 6 are completely closed by trades 22-27.
        # Trade 4 has 70 of 100 units closed by trade 28.
        matchedTrades = [
            (4, 28, Decimal("-70")),
            (6, 27, Decimal("-70")),
            (6, 28, Decimal("-30")),
            (12, 22, Decimal("-125")),
            (13, 22, Decimal("-61")),
            (14, 22, Decimal("-72")),
            (14, 23, Decimal("-200")),
            (14, 24, Decimal("-200")),
            (14, 25, Decimal("-100")),
            (14, 26, Decimal("-242")),
        ]

        # Trade 4 above was partially closed - 30/100 units remain open
        partial = (4, Decimal("-30"))

        self._testTradeSort(MINGAIN, matchedTrades, partial)

    def testMaxGainTrade(self):
        """
        Test MAXGAIN on a series of trades
        """
        # Trades 15-18 and 20 are completely closed by trades 22-26.
        # Trade 21 has 370 of 1000 units closed by trades 26-28.
        matchedTrades = [
            (15, 22, Decimal("-1")),
            (18, 22, Decimal("-200")),
            (16, 22, Decimal("-57")),
            (16, 23, Decimal("-200")),
            (16, 24, Decimal("-200")),
            (16, 25, Decimal("-36")),
            (17, 25, Decimal("-64")),
            (17, 26, Decimal("-36")),
            (20, 26, Decimal("-6")),
            (21, 26, Decimal("-200")),
            (21, 27, Decimal("-70")),
            (21, 28, Decimal("-100")),
        ]

        # Trade 21 above was partially closed - 630/1000 units remain open
        partial = (21, Decimal("-630"))

        self._testTradeSort(MAXGAIN, matchedTrades, partial)

    def _testTradeSort(self, sort, matchedTrades, partialClose):
        """
        Args:
            sort: FIFO/LIFO/MAXGAIN/MINGAIN/None/list of Trade.ids
            matchedTrades: tuple of (open index, close index, units)
            partialClose: tuple of (index, units)
        """
        # Predict the Gains that will be generated by booking the Transactions
        def matchTrades(indexopen, indexclose, units):
            opentx = self.trades[indexopen]
            closetx = self.trades[indexclose]
            lot = Lot(
                opentransaction=opentx,
                createtransaction=opentx,
                units=units,
                price=abs(opentx.cash / opentx.units),
                currency=opentx.currency,
            )
            return Gain(
                lot=lot, transaction=closetx, price=abs(closetx.cash / closetx.units)
            )

        testGains = [matchTrades(*matchedTrade) for matchedTrade in matchedTrades]

        # Book the trades and collect the Gains
        portfolio = Portfolio()
        gains = []
        for t in self.trades:
            g = portfolio.book(t, sort=sort)
            gains.extend(g)

        testGains.sort(
            key=lambda x: str(x.lot.opentransaction.uniqueid)
        )
        gains.sort(key=lambda x: str(x.lot.opentransaction.uniqueid) + str(x.transaction.uniqueid))

        # Generated Gains should match prediction
        self.assertEqual(len(gains), len(testGains))

        for i, gain in enumerate(gains):
            testGain = testGains[i]
            self.assertEqual(gain.lot.opentransaction, testGain.lot.opentransaction)
            self.assertEqual(gain.lot.createtransaction, testGain.lot.createtransaction)
            self.assertEqual(gain.lot.units, testGain.lot.units)
            self.assertEqual(gain.lot.price, testGain.lot.price)
            self.assertEqual(gain.lot.currency, testGain.lot.currency)
            self.assertEqual(gain.transaction, testGain.transaction)

        # The rest of the trades up to the covering buys remain open
        testLots = []
        for i in range(0, 22):
            t = self.trades[i]
            testLots.append(
                Lot(
                    opentransaction=t,
                    createtransaction=t,
                    units=t.units,
                    price=abs(t.cash / t.units),
                    currency=t.currency,
                )
            )
        indices = list({matchedTrade[0] for matchedTrade in matchedTrades})
        indices.sort(reverse=True)
        for i in indices:
            del testLots[i]

        partialindex, partialunits = partialClose
        partial = self.trades[partialindex]
        testLots.append(
            Lot(
                opentransaction=partial,
                createtransaction=partial,
                units=partialunits,
                price=abs(partial.cash / partial.units),
                currency=partial.currency,
            )
        )
        testLots.sort(**FIFO)
        position = portfolio[(None, None)]
        position.sort(**FIFO)

        self.assertEqual(len(position), len(testLots))
        for i, lot in enumerate(position):
            testLot = testLots[i]
            self.assertEqual(lot, testLot)


class ReturnOfCapitalTestCase(unittest.TestCase):
    def setUp(self):
        tx1 = Trade(
            uniqueid="",
            datetime=datetime(2016, 1, 1),
            fiaccount="",
            security="",
            units=Decimal("100"),
            cash=Decimal("1000"),
            currency="USD",
        )
        self.lot1 = Lot(
            opentransaction=tx1,
            createtransaction=tx1,
            units=tx1.units,
            price=abs(tx1.cash / tx1.units),
            currency=tx1.currency,
        )

        tx2 = Trade(
            uniqueid="",
            datetime=datetime(2016, 1, 2),
            fiaccount="",
            security="",
            units=Decimal("200"),
            cash=Decimal("2200"),
            currency="USD",
        )
        self.lot2 = Lot(
            opentransaction=tx2,
            createtransaction=tx2,
            units=tx2.units,
            price=abs(tx2.cash / tx2.units),
            currency=tx2.currency,
        )

        tx3 = Trade(
            uniqueid="",
            datetime=datetime(2016, 1, 1),
            fiaccount="",
            security="",
            units=Decimal("300"),
            cash=Decimal("3600"),
            currency="USD",
        )
        tx3c = Trade(
            uniqueid="",
            datetime=datetime(2016, 1, 3),
            fiaccount="",
            security="",
            cash=None,
            currency=None,
            units=None,
        )
        self.lot3 = Lot(
            opentransaction=tx3,
            createtransaction=tx3c,
            units=tx3.units,
            price=abs(tx3.cash / tx3.units),
            currency=tx3.currency,
        )

        self.portfolio = Portfolio({(None, None): [self.lot1, self.lot2, self.lot3]})

    def testRetOfCapBasic(self):
        """ Test ReturnOfCapital less than basis reduces cost without gain """
        transaction = ReturnOfCapital(
            uniqueid="a",
            datetime=datetime(2016, 1, 4),
            fiaccount=None,
            security=None,
            cash=Decimal("600"),
            currency="USD",
        )
        gains = self.portfolio.book(transaction)
        self.assertEqual(len(gains), 0)
        position = self.portfolio[(None, None)]
        self.assertEqual(position[0], self.lot1._replace(price=Decimal("9")))
        self.assertEqual(position[1], self.lot2._replace(price=Decimal("10")))
        self.assertEqual(position[2], self.lot3._replace(price=Decimal("11")))

    def testRetOfCapDatetime(self):
        """ Test ReturnOfCapital respects Lot.createdt """
        transaction = ReturnOfCapital(
            uniqueid="a",
            datetime=datetime(2016, 1, 2, 1),
            fiaccount=None,
            security=None,
            cash=Decimal("600"),
            currency="USD",
        )
        gains = self.portfolio.book(transaction)
        self.assertEqual(len(gains), 0)
        position = self.portfolio[(None, None)]
        self.assertEqual(position[0], self.lot1._replace(price=Decimal("8")))
        self.assertEqual(position[1], self.lot2._replace(price=Decimal("9")))
        # Lot 3 has opendt before the ReturnOfCapital.datetime, but createdt
        # afterwards - it should follow the createdt and NOT reduce basis
        self.assertEqual(position[2], self.lot3._replace(price=Decimal("12")))

    def testRetOfCapZero(self):
        """ Test ReturnOfCapital reduce basis to zero """
        transaction = ReturnOfCapital(
            uniqueid="a",
            datetime=datetime(2016, 1, 4),
            fiaccount=None,
            security=None,
            cash=Decimal("6000"),
            currency="USD",
        )
        gains = self.portfolio.book(transaction)
        # Lot 1 cost should be reduced to zero but no Gain generated
        self.assertEqual(len(gains), 0)
        position = self.portfolio[(None, None)]
        self.assertEqual(position[0], self.lot1._replace(price=Decimal("0")))
        self.assertEqual(position[1], self.lot2._replace(price=Decimal("1")))
        self.assertEqual(position[2], self.lot3._replace(price=Decimal("2")))

    def testRetOfCapLessThanZero(self):
        """ Test ReturnOfCapital in excess of cost basis """
        transaction = ReturnOfCapital(
            uniqueid="a",
            datetime=datetime(2016, 1, 4),
            fiaccount=None,
            security=None,
            cash=Decimal("7200"),
            currency="USD",
        )
        gains = self.portfolio.book(transaction)
        # Lot 1 & 2 cost should be reduced to zero with Gain generated
        position = self.portfolio[(None, None)]
        self.assertEqual(position[0], self.lot1._replace(price=Decimal("0")))
        self.assertEqual(position[1], self.lot2._replace(price=Decimal("0")))
        # Lot 3 cost should be reduced to zero with no Gain generated
        self.assertEqual(position[2], self.lot3._replace(price=Decimal("0")))

        # Gains should store Lot instances with full price (not reduced
        # for the ReturnOfCapital)
        self.assertEqual(len(gains), 2)
        gain0 = gains[0]
        self.assertEqual(gain0.lot, self.lot1)
        self.assertEqual(gain0.transaction, transaction)
        self.assertEqual(gain0.price, Decimal("12"))  # $7,200 over 600sh
        gain1 = gains[1]
        self.assertEqual(gain1.lot, self.lot2)
        self.assertEqual(gain1.transaction, transaction)
        self.assertEqual(gain1.price, Decimal("12"))  # $7,200 over 600sh
        self.assertEqual(gain1.lot.price, Decimal("11"))

    def testRetOfCapMultiplePositions(self):
        """
        Test Portfolio route ReturnOfCapital to correct (account, security)
        """
        tx4 = Trade(
            uniqueid="",
            datetime=datetime(2016, 1, 1),
            fiaccount="",
            security="",
            units=Decimal("100"),
            cash=Decimal("1000"),
            currency="USD",
        )
        lot4 = Lot(
            opentransaction=tx4,
            createtransaction=tx4,
            units=tx4.units,
            price=abs(tx4.cash / tx4.units),
            currency=tx4.currency,
        )

        tx5 = Trade(
            uniqueid="",
            datetime=datetime(2016, 1, 2),
            fiaccount="",
            security="",
            units=Decimal("200"),
            cash=Decimal("2200"),
            currency="USD",
        )
        lot5 = Lot(
            opentransaction=tx5,
            createtransaction=tx5,
            units=tx5.units,
            price=abs(tx5.cash / tx5.units),
            currency=tx5.currency,
        )

        tx6 = Trade(
            uniqueid="",
            datetime=datetime(2016, 1, 2),
            fiaccount="",
            security="",
            units=Decimal("300"),
            cash=Decimal("3600"),
            currency="USD",
        )
        lot6 = Lot(
            opentransaction=tx6,
            createtransaction=tx6,
            units=tx6.units,
            price=abs(tx6.cash / tx6.units),
            currency=tx6.currency,
        )

        self.portfolio[(None, "sec4")].append(lot4)
        self.portfolio[("acct5", "sec5")].append(lot5)
        self.portfolio[("acct6", None)].append(lot6)

        # This routes to (None, None) - [self.lot1, self.lot2, self.lot3]; 600sh
        retofcap1 = ReturnOfCapital(
            uniqueid="",
            fiaccount=None,
            security=None,
            datetime=datetime(2016, 6, 1),
            cash=Decimal("1200"),
            currency="USD",
        )
        # This routes to ('acct6', None) - lot6; 300sh
        retofcap2 = ReturnOfCapital(
            uniqueid="",
            fiaccount="acct6",
            security=None,
            datetime=datetime(2016, 6, 1),
            cash=Decimal("600"),
            currency="USD",
        )
        # This routes to (None, 'sec4') - lot4; 100sh
        retofcap3 = ReturnOfCapital(
            uniqueid="",
            fiaccount=None,
            security="sec4",
            datetime=datetime(2016, 6, 1),
            cash=Decimal("300"),
            currency="USD",
        )
        # This routes to ('acct5', 'sec5') - lot5; 200sh
        retofcap4 = ReturnOfCapital(
            uniqueid="",
            fiaccount="acct5",
            security="sec5",
            datetime=datetime(2016, 6, 1),
            cash=Decimal("800"),
            currency="USD",
        )
        for retofcap in (retofcap1, retofcap2, retofcap3, retofcap4):
            self.portfolio.book(retofcap)

        position = self.portfolio[(None, None)]
        self.assertEqual(len(position), 3)
        self.assertEqual(position[0], self.lot1._replace(price=Decimal("8")))
        self.assertEqual(position[1], self.lot2._replace(price=Decimal("9")))
        self.assertEqual(position[2], self.lot3._replace(price=Decimal("10")))

        position = self.portfolio[(None, "sec4")]
        self.assertEqual(len(position), 1)
        self.assertEqual(position[0], lot4._replace(price=Decimal("7")))

        position = self.portfolio[("acct5", "sec5")]
        self.assertEqual(len(position), 1)
        self.assertEqual(position[0], lot5._replace(price=Decimal("7")))

        position = self.portfolio[("acct6", None)]
        self.assertEqual(len(position), 1)
        self.assertEqual(position[0], lot6._replace(price=Decimal("10")))


class SplitTestCase(unittest.TestCase):
    def setUp(self):
        tx0 = Trade(
            datetime=datetime(2016, 1, 1),
            uniqueid="",
            fiaccount=None,
            security=None,
            units=Decimal("100"),
            cash=Decimal("-1000"),
            currency="USD",
        )
        self.lot0 = Lot(
            opentransaction=tx0,
            createtransaction=tx0,
            units=tx0.units,
            price=abs(tx0.cash / tx0.units),
            currency=tx0.currency,
        )

        tx1 = Trade(
            datetime=datetime(2016, 1, 3),
            uniqueid="",
            fiaccount=None,
            security=None,
            units=Decimal("300"),
            cash=Decimal("-3600"),
            currency="USD",
        )
        self.lot1 = Lot(
            opentransaction=tx1,
            createtransaction=tx1,
            units=tx1.units,
            price=abs(tx1.cash / tx1.units),
            currency=tx1.currency,
        )

        self.portfolio = Portfolio({(None, None): [self.lot0, self.lot1]})

    def testSplitDatetime(self):
        """ Splits respect Lot.createdt not Lot.opendt """
        split = Split(
            datetime=datetime(2016, 1, 2),
            uniqueid=None,
            fiaccount=None,
            security=None,
            numerator=Decimal("1"),
            denominator=Decimal("10"),
            units=Decimal("-90"),
        )

        gains = self.portfolio.book(split)
        self.assertEqual(len(gains), 0)
        position = self.portfolio[(None, None)]
        self.assertEqual(len(position), 2)
        self.assertEqual(position[0], self.lot0._replace(units=10, price=100))
        self.assertEqual(position[1], self.lot1)

    def testSplitWrongUnits(self):
        """
        Split.units must match total Lot.units before
        Split.datetime
        """
        split = Split(
            datetime=datetime(2016, 1, 2),
            uniqueid="",
            fiaccount=None,
            security=None,
            numerator=Decimal("1"),
            denominator=Decimal("10"),
            units=Decimal("90"),
        )
        with self.assertRaises(Inconsistent):
            self.portfolio.book(split)


class TransferTestCase(unittest.TestCase):
    def setUp(self):
        tx1 = Trade(
            uniqueid="",
            fiaccount=None,
            datetime=datetime(2016, 1, 1),
            security=1,
            units=Decimal("100"),
            cash=Decimal("-1000"),
            currency="USD",
        )
        self.lot1 = Lot(
            opentransaction=tx1,
            createtransaction=tx1,
            units=tx1.units,
            price=abs(tx1.cash / tx1.units),
            currency=tx1.currency,
        )
        tx2 = Trade(
            uniqueid="",
            fiaccount=None,
            datetime=datetime(2016, 1, 1),
            security=2,
            units=Decimal("-300"),
            cash=Decimal("3600"),
            currency="USD",
        )
        self.lot2 = Lot(
            opentransaction=tx2,
            createtransaction=tx2,
            units=tx2.units,
            price=abs(tx1.cash / tx1.units),
            currency="USD",
        )

        self.portfolio = Portfolio({(None, 1): [self.lot1], (None, 2): [self.lot2]})

    def testTransfer(self):
        """
        Transfer divides cost and preserves holding period
        """
        transfer = Transfer(
            uniqueid="",
            fiaccount=None,
            fromfiaccount=None,
            datetime=datetime(2016, 1, 4),
            security=3,
            units=Decimal("100"),
            fromsecurity=1,
            fromunits=Decimal("-50"),
        )
        gains = self.portfolio.book(transfer)
        self.assertEqual(len(gains), 0)

        # Half of lot1 units were transferred out; everything else is the same
        pos1 = self.portfolio[(None, 1)]
        self.assertEqual(len(pos1), 1)
        self.assertEqual(pos1[0], self.lot1._replace(units=50))

        # Holding period was preserved
        pos3 = self.portfolio[(None, 3)]
        self.assertEqual(len(pos3), 1)
        lot = pos3[0]
        self.assertEqual(lot.opentransaction, self.lot1.opentransaction)
        self.assertEqual(lot.createtransaction, transfer)
        self.assertEqual(lot.units, transfer.units)
        self.assertEqual(
            lot.price, self.lot1.price * -transfer.fromunits / transfer.units
        )
        self.assertEqual(lot.currency, self.lot1.currency)

    def testTransferClose(self):
        """
        Transfer correctly closes oppositely-signed Lots of transfer Security
        """
        transfer = Transfer(
            uniqueid="",
            datetime=datetime(2016, 1, 4),
            fiaccount=None,
            fromfiaccount=None,
            security=2,
            units=Decimal("100"),
            fromsecurity=1,
            fromunits=Decimal("-50"),
        )
        gains = self.portfolio.book(transfer)

        pos1 = self.portfolio[(None, 1)]
        self.assertEqual(len(pos1), 1)
        self.assertEqual(pos1[0], self.lot1._replace(units=50))

        pos2 = self.portfolio[(None, 2)]
        self.assertEqual(len(pos2), 1)
        self.assertEqual(pos2[0], self.lot2._replace(units=-200))

        self.assertEqual(len(gains), 1)
        gain = gains[0]
        self.assertEqual(gain.lot, self.lot2._replace(units=-100))
        self.assertEqual(gain.transaction, transfer)

    def testTransferBadTransaction(self):
        """
        Transactions that can't be satisfied raise errors.
        """
        # fromunits and units must have opposite signs
        transfer = Transfer(
            uniqueid="",
            datetime=datetime(2016, 1, 4),
            fiaccount=None,
            fromfiaccount=None,
            security=2,
            units=Decimal("100"),
            fromsecurity=1,
            fromunits=Decimal("50"),
        )
        with self.assertRaises(ValueError):
            self.portfolio.book(transfer)

        # Must have an existing position in (accountfrom, fromsecurity)
        transfer = Transfer(
            uniqueid="",
            datetime=datetime(2016, 1, 4),
            fiaccount=None,
            fromfiaccount=None,
            security=2,
            units=Decimal("100"),
            fromsecurity=3,
            fromunits=Decimal("-50"),
        )
        with self.assertRaises(Inconsistent):
            self.portfolio.book(transfer)

        # Existing position must have enough units to satisfy fromunits
        transfer = Transfer(
            uniqueid="",
            datetime=datetime(2016, 1, 4),
            fiaccount=None,
            fromfiaccount=None,
            security=2,
            units=Decimal("100"),
            fromsecurity=1,
            fromunits=Decimal("-150"),
        )
        with self.assertRaises(Inconsistent):
            self.portfolio.book(transfer)


class SpinoffTestCase(unittest.TestCase):
    def setUp(self):
        tx1 = Trade(
            uniqueid="",
            datetime=datetime(2016, 1, 1),
            fiaccount=None,
            security=1,
            units=Decimal("100"),
            cash=Decimal("-1000"),
            currency="USD",
        )
        self.lot1 = Lot(
            opentransaction=tx1,
            createtransaction=tx1,
            units=tx1.units,
            price=abs(tx1.cash / tx1.units),
            currency=tx1.currency,
        )

        tx2 = Trade(
            uniqueid="",
            datetime=datetime(2016, 1, 1),
            fiaccount=None,
            security=2,
            units=Decimal("-300"),
            cash=Decimal("3600"),
            currency="USD",
        )
        self.lot2 = Lot(
            opentransaction=tx2,
            createtransaction=tx2,
            units=tx2.units,
            price=abs(tx2.cash / tx2.units),
            currency=tx2.currency,
        )

        self.portfolio = Portfolio({(None, 1): [self.lot1], (None, 2): [self.lot2]})

    def testSpinoff(self):
        """
        Spinoff divides cost and preserves holding period
        """
        # 1 for 5 on 100sh: spin 20sh@5; retain 100sh@1
        spinoff = Spinoff(
            uniqueid=None,
            datetime=datetime(2016, 1, 4),
            fiaccount=None,
            security=3,
            numerator=Decimal("1"),
            denominator=Decimal("5"),
            units=Decimal("20"),
            fromsecurity=1,
            securityprice=Decimal("5"),
            fromsecurityprice=Decimal("1"),
        )
        gains = self.portfolio.book(spinoff)
        self.assertEqual(len(gains), 0)

        # Half the original cost is left in lot1; everything else is the same
        position1 = self.portfolio[(None, 1)]
        self.assertEqual(len(position1), 1)
        lot1 = position1[0]
        self.assertEqual(lot1, self.lot1._replace(price=5))

        # Half the original cost of lot1 was spun off to security3
        position3 = self.portfolio[(None, 3)]
        self.assertEqual(len(position3), 1)
        lot3 = position3[0]
        self.assertIs(lot3.opentransaction, self.lot1.opentransaction)
        self.assertIs(lot3.createtransaction, spinoff)
        self.assertEqual(lot3.units, spinoff.units)
        self.assertEqual(lot3.price, Decimal("25"))
        self.assertEqual(lot3.currency, self.lot1.currency)

        # Aggregate cost is conserved over the spinoff
        self.assertEqual(
            sum([l.units * l.price for l in position1])
            + sum([l.units * l.price for l in position3]),
            self.lot1.units * self.lot1.price,
        )

    def testSpinoffClose(self):
        """
        Spinoff correctly closes oppositely-signed Lots of spin Security
        """
        # 1 for 5 on 100sh: spin 20sh@5; retain 100sh@1
        spinoff = Spinoff(
            datetime=datetime(2016, 1, 4),
            uniqueid=None,
            fiaccount=None,
            security=2,
            numerator=Decimal("1"),
            denominator=Decimal("5"),
            units=Decimal("20"),
            fromsecurity=1,
            securityprice=Decimal("5"),
            fromsecurityprice=Decimal("1"),
        )
        gains = self.portfolio.book(spinoff)
        self.assertEqual(len(gains), 1)
        gain = gains.pop()
        lot = gain.lot
        # Half the original cost of lot1 was spun off; closed some of lot2
        self.assertEqual(lot, self.lot2._replace(units=-20))
        self.assertEqual(gain.transaction, spinoff)

        # Half the original cost is left in lot1
        position1 = self.portfolio[(None, 1)]
        self.assertEqual(len(position1), 1)
        lot1 = position1[0]
        self.assertEqual(lot1, self.lot1._replace(price=5))

        # The spunoff shares closed 20 units of security 2
        position2 = self.portfolio[(None, 2)]
        self.assertEqual(len(position2), 1)
        lot2 = position2[0]
        self.assertEqual(lot2, self.lot2._replace(units=-280))


if __name__ == "__main__":
    unittest.main()
