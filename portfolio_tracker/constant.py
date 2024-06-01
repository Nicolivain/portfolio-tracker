from enum import Enum


class BudgettingColumns(Enum):
    date = "dateOp"
    category = "categoryParent"
    subcategory = "category"
    amount = "amount"
    description = "label"
    account = "accountNum"
    bank = "accountLabel"
    receiver = "supplierFound"
    tags = "Tags"
    notes = "comment"
    

class Side(Enum):
    buy = "Buy"
    sell = "Sell"
    deposit = "Deposit"
    withdrawal = "Withdrawal"


class MovementType(Enum):
    deposit = "Deposit"
    withdrawal = "Withdrawal"
    interest = "Interest"
    fees = "Fees"
    taxes = "Taxes"
    taxes_dvd = "Taxes dvd"


class MovementColumns(Enum):
    date = "Date"
    account = "Account"
    side = "D/W"
    qty = "Amount"
    desc = "Description"
    type = "Type"
    currency = "Currency"


class OrderColumns(Enum):
    position_open_date = "_position_open_date"
    date = "Date"
    portfolio = "Portfolio"
    instrument = "Instrument"
    market = "Market"
    sym = "Symbol"
    side = "Side"
    qty = "Quantity"
    unit_cost = "Unit Cost"
    book_cost = "Book Cost"
    fees = "Fees"
    taxes = "Taxes"
    total_cost = "Total Cost"


class PortfolioColumns(Enum):
    date = "Date"
    local_ccy = "Currency"
    instrument = "Instrument"
    market = "Market"
    sym = "Symbol"
    qty = "Quantity"
    price = "Current Price"
    unit_cost = "Unit Cost"
    fees = "Fees"
    taxes = "Taxes"

    value_local_currency = "Valorisation Local Ccy"
    value_book_currency = "Valorisation Reporting Ccy"
    delta = "Delta"
    dividends = "Dividends"

    returns = "Returns"
    yld = "Ann. Returns"
    sharpe = "Sharpe ratio"

    gross_profits = "ROI Gross"
    net_profits = "ROI Net"


class YFinanceColumns(Enum):
    date = "Date"
    price = "Close"
    dividends = "Dividends"


class CashAccountSummary(Enum):
    open_date = "Date ouverture"
    account = "Account"
    balance = "Balance"
    interest = "Interests"
    taxes = "Taxes"
    fees = "Taxes"
    pct = "Capital Allocation"
    value_euro = "Valorisation Reporting Ccy"


class PortfolioSummary(Enum):
    open_date = "Opening Data"
    account = "Account"
    deposits = "Investments"
    value = "Valorisation"
    returns = "Returns"
    yld = "Ann. Returns"
    fees = "Fees"
    taxes = "Taxes"
    sharpe = "Sharpe"
    volatility = "Volatilite"
    max_drawdown = "Max Drawdown"
    pct = "Capital Allocation"
    value_euro = "Valorisation Reporting Ccy"


MARKET_MAP = {"XLON": "L", "XSTO": "ST", "XPAR": "PA"}

SIDE_TO_IBUY = {Side.buy: 1, Side.sell: -1, Side.deposit: 1, Side.withdrawal: -1}

PORTFOLIO_DISPLAY_ORDER = [
    PortfolioColumns.sym.value,
    PortfolioColumns.market.value,
    PortfolioColumns.date.value,
    PortfolioColumns.local_ccy.value,
    PortfolioColumns.qty.value,
    PortfolioColumns.unit_cost.value,
    PortfolioColumns.price.value,
    PortfolioColumns.value_local_currency.value,
    PortfolioColumns.value_book_currency.value,
    PortfolioColumns.delta.value,
    PortfolioColumns.dividends.value,
    PortfolioColumns.gross_profits.value,
    PortfolioColumns.net_profits.value,
    PortfolioColumns.returns.value,
    PortfolioColumns.yld.value,
    PortfolioColumns.sharpe.value,
]

CASH_ACCOUNT_SUMMARY_DISPLAY_ORDER = [
    CashAccountSummary.balance.value,
    CashAccountSummary.balance.value,
    CashAccountSummary.interest.value,
    CashAccountSummary.fees.value,
    CashAccountSummary.taxes.value,
    CashAccountSummary.value_euro.value_euro,
    CashAccountSummary.pct.value_euro,
]

PORTFOLIO_SUMMARY_DISPLAY_ORDER = [
    PortfolioSummary.open_date.value,
    PortfolioSummary.account.value,
    PortfolioSummary.deposits.value,
    PortfolioSummary.returns.value,
    PortfolioSummary.value.value,
    PortfolioSummary.returns.value,
    PortfolioSummary.yld.value,
    PortfolioSummary.fees.value,
    PortfolioSummary.taxes.value,
    PortfolioSummary.sharpe.value,
    PortfolioSummary.volatility.value,
    PortfolioSummary.max_drawdown.value,
    PortfolioSummary.pct.value,
    PortfolioSummary.value_euro.value,
]
