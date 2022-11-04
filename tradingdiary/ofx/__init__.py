import ofxtools

from . import reader


def read(session, source):
    # Avoid import loop by delaying import until after module initialization
    from tradingdiary.ofx.reader import OfxStatementReader
    from tradingdiary.ofx import ibkr, amtd, etfc, scottrade

    dispatcher = {
        ibkr.BROKERID: ibkr.OfxStatementReader,
        amtd.BROKERID: amtd.OfxStatementReader,
        etfc.BROKERID: etfc.OfxStatementReader,
        scottrade.BROKERID: scottrade.OfxStatementReader,
    }

    ofxtree = ofxtools.OFXTree()
    ofxtree.parse(source)
    ofx = ofxtree.convert()

    transactions = []
    for stmt in ofx.statements:
        # We only want INVSTMTRS
        if not isinstance(stmt, ofxtools.models.INVSTMTRS):
            continue
        fromacct = stmt.account
        # Look up OfxReader subclass by brokerid
        Reader = dispatcher.get(fromacct.brokerid, OfxStatementReader)
        # Initialize reader instance with INVSTMTRS, SECLIST
        rdr = Reader(stmt, ofx.securities)
        rdr.read(session)
        transactions.extend(rdr.transactions)
    return transactions
