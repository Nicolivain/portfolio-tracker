from enum import Enum

### Budgetting Constants ###

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
    buy = "Achat"
    sell = "Vente"
    deposit = "Depot"
    withdrawal = "Retrait"


class MovementType(Enum):
    deposit = "Depot"
    withdrawal = "Retrait"
    interest = "Interet"
    fees = "Frais"
    taxes = "Taxes"
    taxes_dvd = "Taxes dvd"


class MovementColumns(Enum):
    date = "Date"
    account = "Compte"
    side = "Depot/Retrait"
    qty = "Montant"
    desc = "Description"
    type = "Type"
    currency = "Devise"


class OrderColumns(Enum):
    position_open_date = "_position_open_date"
    date = "Date"
    portfolio = "Portefeuille"
    instrument = "Instrument"
    market = "Marche"
    sym = "Symbole"
    side = "Achat/Vente"
    qty = "Unites"
    unit_cost = "PRU"
    book_cost = "Book Cost"
    fees = "Frais"
    taxes = "Taxes"
    total_cost = "Cout Total"


class PortfolioColumns(Enum):
    date = "Date"
    local_ccy = "Devise"
    instrument = "Instrument"
    market = "Marche"
    sym = "Symbole"
    qty = "Unites"
    price = "Prix"
    unit_cost = "PRU"
    fees = "Frais"
    taxes = "Taxes"

    value_local_currency = "Valorisation"
    value_book_currency = "Valorisation Portefeuille"
    delta = "Delta"
    dividends = "Dividendes Percus"

    returns = "Rendement"
    yld = "Yield"
    sharpe = "Sharpe ratio"

    gross_profits = "ROI Brut"
    net_profits = "ROI Net"


class YFinanceColumns(Enum):
    date = "Date"
    price = "Close"
    dividends = "Dividends"


class CashAccountSummary(Enum):
    open_date = "Date ouverture"
    account = "Compte"
    balance = "Balance"
    interest = "Interets"
    taxes = "Taxes"
    fees = "Frais"
    pct = "Proportion Capital"
    value_euro = "Valorisation Euro"


class PortfolioSummary(Enum):
    open_date = "Date ouverture"
    account = "Compte"
    deposits = "Investissements"
    value = "Valorisation"
    returns = "Rendement"
    yld = "Yield"
    fees = "Frais"
    taxes = "Taxes"
    sharpe = "Sharpe"
    volatility = "Volatilite"
    max_drawdown = "Max Drawdown"
    pct = "Proportion Capital"
    value_euro = "Valorisation Euro"


MARKET_MAP = {"XLON": "L", "XSTO": "ST"}

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
