import datetime as dt
from enum import Enum
from typing import Dict, Type

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import xlwings as xw

from constant import (
    OrderColumns,
    MovementColumns,
    MovementType,
    PortfolioColumns,
    YFinanceColumns,
    CashAccountSummary,
    PortfolioSummary,
    Side,
    SIDE_TO_IBUY,
    PORTFOLIO_DISPLAY_ORDER,
)
from portfolio_utils import (
    compute_sharpe_ratio,
    compute_position_value_and_dividend_over_time,
    compute_portfolio_returns_over_time,
    compute_backtest_metrics,
)
from utils import (
    positive_weighted_average,
    get_historical_prices_with_dates,
    get_company_info,
    get_today_forex_rates,
    read_table,
    save_dataframe,
)

matplotlib.use("Agg")


def compute_signed_quantity(df: pd.DataFrame, cols: Type[Enum]):
    df[cols.side.value] = df[cols.side.value].apply(Side)
    df[cols.side.value] = df[cols.side.value].apply(lambda s: SIDE_TO_IBUY[s])
    df[cols.qty.value] *= df[cols.side.value]
    return df


def aggregate_orders_to_portfolio_df(order_data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    portfolios = {}
    all_portfolio = order_data[OrderColumns.portfolio.value].unique()
    for portfolio_key in all_portfolio:
        sub_df = order_data[order_data[OrderColumns.portfolio.value] == portfolio_key].copy()
        grouped_df = sub_df.groupby([OrderColumns.sym.value, OrderColumns.market.value])

        avg_unit_cost = grouped_df.apply(
            positive_weighted_average, OrderColumns.unit_cost.value, OrderColumns.qty.value
        )
        total_dividend_earned = grouped_df.apply(lambda g: compute_position_value_and_dividend_over_time(g)[1].sum())
        portfolio_df = grouped_df.agg(
            {
                OrderColumns.date.value: "last",
                OrderColumns.qty.value: "sum",
                OrderColumns.fees.value: "sum",
                OrderColumns.taxes.value: "sum",
            }
        )
        portfolio_df[PortfolioColumns.unit_cost.value] = avg_unit_cost
        portfolio_df[PortfolioColumns.dividends.value] = total_dividend_earned

        portfolios[portfolio_key] = portfolio_df
    return portfolios


def build_portfolio_analytics(portfolio_df: pd.DataFrame, book_currency: str) -> pd.DataFrame:
    portfolio_df[
        [
            PortfolioColumns.value_local_currency.value,
            PortfolioColumns.value_book_currency.value,
            PortfolioColumns.delta.value,
            PortfolioColumns.returns.value,
            PortfolioColumns.sharpe.value,
            PortfolioColumns.gross_profits.value,
            PortfolioColumns.net_profits.value,
        ]
    ] = 0.0

    print(portfolio_df)
    today = dt.date.today()

    for sym, market in portfolio_df.index:
        idx = (sym, market)
        date = portfolio_df.loc[idx, PortfolioColumns.date.value].date()
        historical_data = get_historical_prices_with_dates(sym, market, date, today)
        instrument_name, local_ccy = get_company_info(sym, market)

        today_price_local_ccy = historical_data[YFinanceColumns.price.value].iloc[-1]

        fx_rate = 1
        if local_ccy != book_currency:
            if local_ccy == "GBp" and book_currency == "GBP":
                # fx_rate = 1 / 100
                today_price_local_ccy /= 100
                portfolio_df.loc[idx, PortfolioColumns.dividends.value] /= 100
            elif local_ccy == "GBp":
                fx_rate = get_today_forex_rates("GBP", book_currency) / 100
            else:
                fx_rate = get_today_forex_rates(local_ccy, book_currency)
        historical_data[[YFinanceColumns.price.value, YFinanceColumns.dividends.value]] *= fx_rate

        # Adding the metrics to the DataFrame
        portfolio_df.loc[idx, PortfolioColumns.local_ccy.value] = local_ccy
        portfolio_df.loc[idx, PortfolioColumns.price.value] = today_price_local_ccy
        portfolio_df.loc[idx, PortfolioColumns.value_local_currency.value] = (
            portfolio_df.loc[idx, PortfolioColumns.qty.value] * today_price_local_ccy
        )
        portfolio_df.loc[idx, PortfolioColumns.value_book_currency.value] = (
            portfolio_df.loc[idx, PortfolioColumns.value_local_currency.value] * fx_rate
        )
        portfolio_df.loc[idx, PortfolioColumns.sharpe.value] = compute_sharpe_ratio(historical_data)
        portfolio_df.loc[idx, PortfolioColumns.dividends.value] *= fx_rate

    # Adding the remaining metrics to the DataFrame in a vectorized way
    portfolio_df[PortfolioColumns.delta.value] = (
        portfolio_df[PortfolioColumns.value_book_currency.value]
        - portfolio_df[PortfolioColumns.unit_cost.value] * portfolio_df[PortfolioColumns.qty.value]
    )
    portfolio_df[PortfolioColumns.gross_profits.value] = (
        portfolio_df[PortfolioColumns.delta.value] + portfolio_df[PortfolioColumns.dividends.value]
    )
    portfolio_df[PortfolioColumns.net_profits.value] = (
        portfolio_df[PortfolioColumns.gross_profits.value]
        - portfolio_df[PortfolioColumns.taxes.value]
        - portfolio_df[PortfolioColumns.fees.value]
    )
    portfolio_df[PortfolioColumns.returns.value] = portfolio_df[PortfolioColumns.net_profits.value] / (
        portfolio_df[PortfolioColumns.qty.value] * portfolio_df[PortfolioColumns.unit_cost.value]
    )
    portfolio_df[PortfolioColumns.yld.value] = (
        portfolio_df[PortfolioColumns.returns.value]
        * 365
        / (dt.date.today() - portfolio_df[PortfolioColumns.date.value].dt.date).apply(lambda x: x.days)
    )
    return portfolio_df.reset_index()


def build_cash_accounts_summary(
    mvt_df: pd.DataFrame,
    order_df: pd.DataFrame,
    portfolios: Dict[str, pd.DataFrame],
    book_currencies: Dict[str, str],
    master_currency="EUR",
):
    cash_account_names = mvt_df[MovementColumns.account.value].unique().tolist()
    cash_accounts = []

    for key in cash_account_names:
        assert (
            mvt_df.loc[mvt_df[MovementColumns.account.value] == key, MovementColumns.currency.value]
        ).nunique() == 1, "Cash Accounts only support one currency."
        local_currency = mvt_df.loc[mvt_df[MovementColumns.account.value] == key, MovementColumns.currency.value].iloc[
            0
        ]
        assert (
            key in portfolios and book_currencies.get(key, master_currency) == local_currency
        ) or key not in portfolios, "Cash account currency must be the same as book currency."

        fx_rate = 1
        if local_currency != master_currency:
            fx_rate = get_today_forex_rates(local_currency, master_currency)

        open_date = mvt_df.loc[mvt_df[MovementColumns.account.value] == key, MovementColumns.date.value].min()
        balance = mvt_df.loc[mvt_df[MovementColumns.account.value] == key, MovementColumns.qty.value].sum()
        interest = mvt_df.loc[
            (mvt_df[MovementColumns.account.value] == key)
            & (mvt_df[MovementColumns.type.value] == MovementType.interest.value),
            MovementColumns.qty.value,
        ].sum()
        fees = mvt_df.loc[
            (mvt_df[MovementColumns.account.value] == key)
            & (mvt_df[MovementColumns.type.value] == MovementType.fees.value),
            MovementColumns.qty.value,
        ].sum()
        taxes = mvt_df.loc[
            (mvt_df[MovementColumns.account.value] == key)
            & (mvt_df[MovementColumns.type.value] == MovementType.taxes.value),
            MovementColumns.qty.value,
        ].sum()

        row = {
            CashAccountSummary.open_date.value: open_date,
            CashAccountSummary.account.value: key,
            CashAccountSummary.balance.value: balance,
            CashAccountSummary.interest.value: interest,
            CashAccountSummary.fees.value: fees,
            CashAccountSummary.taxes.value: taxes,
        }

        if key in portfolios:
            sub_df = order_df.loc[order_df[OrderColumns.portfolio.value] == key]
            delta = -(sub_df[OrderColumns.book_cost.value] * sub_df[OrderColumns.side.value]).sum()
            delta -= sub_df[OrderColumns.fees.value].sum()
            delta -= sub_df[OrderColumns.taxes.value].sum()
            delta += portfolios[key][PortfolioColumns.dividends.value].sum()
            row[CashAccountSummary.balance.value] += delta
            row[CashAccountSummary.account.value] += " Cash"

        row[CashAccountSummary.value_euro.value] = row[CashAccountSummary.balance.value] * fx_rate
        cash_accounts.append(row)

    cash_accounts_summary = pd.DataFrame.from_records(cash_accounts)
    return cash_accounts_summary


def build_portfolio_summary(
    order_df: pd.DataFrame,
    portfolios: Dict[str, pd.DataFrame],
    book_currencies: Dict[str, str],
    master_currency="EUR",
):
    portfolio_summary_records = []
    for key, portfolio_df in portfolios.items():
        open_date = order_df.loc[order_df[OrderColumns.portfolio.value] == key, OrderColumns.date.value].min()
        book_currency = book_currencies.get(key, master_currency)

        deposits = (portfolio_df[PortfolioColumns.unit_cost.value] * portfolio_df[PortfolioColumns.qty.value]).sum()
        taxes = portfolio_df[PortfolioColumns.taxes.value].sum()
        fees = portfolio_df[PortfolioColumns.fees.value].sum()
        deposits += taxes + fees

        returns_ts = compute_portfolio_returns_over_time(
            order_df.loc[order_df[OrderColumns.portfolio.value] == key, :], book_currency
        )
        sharpe, vol, max_dd = compute_backtest_metrics(returns_ts)

        value_book_currency = portfolio_df[PortfolioColumns.value_book_currency.value].sum()

        fx_rate = 1
        if book_currency != master_currency:
            fx_rate = get_today_forex_rates(book_currency, master_currency)

        row_dict = {
            PortfolioSummary.open_date.value: open_date,
            PortfolioSummary.account.value: key,
            PortfolioSummary.deposits.value: deposits,
            PortfolioSummary.value.value: value_book_currency,
            PortfolioSummary.taxes.value: taxes,
            PortfolioSummary.fees.value: fees,
            PortfolioSummary.value_euro.value: value_book_currency * fx_rate,
            PortfolioSummary.max_drawdown.value: max_dd,
            PortfolioSummary.volatility.value: vol,
            PortfolioSummary.sharpe.value: sharpe,
        }
        portfolio_summary_records.append(row_dict)

    portfolio_summary = pd.DataFrame.from_records(portfolio_summary_records)

    portfolio_summary[PortfolioSummary.returns.value] = (
        portfolio_summary[PortfolioSummary.value.value] - portfolio_summary[PortfolioSummary.deposits.value]
    ) / portfolio_summary[PortfolioSummary.deposits.value]
    portfolio_summary[PortfolioSummary.yld.value] = (
        portfolio_summary[PortfolioSummary.returns.value]
        * 365
        / (dt.date.today() - portfolio_summary[PortfolioSummary.open_date.value].dt.date).apply(lambda x: x.days)
    )
    return portfolio_summary


def plot_portfolio_returns(portfolio_order_df, start_date, book_currency, title, sheet):
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111)
    portfolio_returns = compute_portfolio_returns_over_time(portfolio_order_df, book_currency)
    cumulative_returns = (1 + portfolio_returns).cumprod().shift(1)
    cumulative_returns.iloc[0] = 1
    mask = pd.to_datetime(cumulative_returns.index) >= start_date
    cumulative_returns[mask].plot(ax=ax)
    ax.set_title(title)
    sheet.pictures.add(fig, name=title, update=True)


def plot_donut_chart(labels, sizes, title, sheet):
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)

    # Create a pie chart
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)

    # Draw a circle at the center of pie chart
    centre_circle = plt.Circle((0, 0), 0.70, fc="white")
    ax.add_artist(centre_circle)

    # Equal aspect ratio ensures that pie is drawn as a circle
    ax.axis("equal")
    ax.set_title(title)
    sheet.pictures.add(fig, name=title, update=True)


def main():
    wb = xw.Book.caller()
    mvt_sheet = wb.sheets["Mouvements"]
    order_sheet = wb.sheets["Ordres"]
    summary_sheet = wb.sheets["Investissement"]

    master_currency = "EUR"
    book_currencies = {"BARC": "GBP"}

    origin = "B2"

    mvt_data = read_table(origin, mvt_sheet).reset_index()
    mvt_data.drop(MovementColumns.desc.value, inplace=True, axis=1)
    mvt_data = compute_signed_quantity(mvt_data, MovementColumns)

    order_data = read_table(origin, order_sheet).reset_index()
    order_data.drop(OrderColumns.instrument.value, inplace=True, axis=1)
    order_data = compute_signed_quantity(order_data, OrderColumns)

    # Generate each portfolio's individual page
    portfolios = aggregate_orders_to_portfolio_df(order_data)
    for portfolio_key, portfolio_df in portfolios.items():
        book_ccy = book_currencies.get(portfolio_key, master_currency)
        portfolio_df = build_portfolio_analytics(portfolio_df, book_ccy)
        to_sheet = wb.sheets[portfolio_key]
        save_dataframe(portfolio_df[PORTFOLIO_DISPLAY_ORDER], origin, to_sheet, index=False)
        plot_portfolio_returns(
            portfolio_order_df=order_data[order_data[OrderColumns.portfolio.value] == portfolio_key],
            start_date=order_data.loc[
                order_data[OrderColumns.portfolio.value] == portfolio_key, OrderColumns.date.value
            ].min(),
            book_currency=book_ccy,
            title="Portfolio performance since inception",
            sheet=to_sheet,
        )
        plot_portfolio_returns(
            portfolio_order_df=order_data[order_data[OrderColumns.portfolio.value] == portfolio_key],
            start_date=pd.to_datetime(dt.date.today() - dt.timedelta(days=365)),
            book_currency=book_ccy,
            title="Portfolio 1Y",
            sheet=to_sheet,
        )
        plot_donut_chart(
            labels=portfolio_df[PortfolioColumns.sym.value],
            sizes=portfolio_df[PortfolioColumns.value_book_currency.value],
            title="Asset Allocation",
            sheet=to_sheet,
        )

    # Compute the overall investment resume
    cash_accounts_summary = build_cash_accounts_summary(
        mvt_data, order_data, portfolios, book_currencies, master_currency
    )
    save_dataframe(cash_accounts_summary, "B8", summary_sheet, index=False)
    portfolio_summary = build_portfolio_summary(order_data, portfolios, book_currencies, master_currency)
    save_dataframe(portfolio_summary, "B20", summary_sheet, index=False)

    plot_portfolio_returns(
        portfolio_order_df=order_data,
        start_date=pd.to_datetime(dt.date.today() - dt.timedelta(days=365)),
        book_currency=master_currency,
        title="Portfolio performance 1Y",
        sheet=summary_sheet,
    )
    plot_portfolio_returns(
        portfolio_order_df=order_data,
        start_date=order_data[OrderColumns.date.value].min(),
        book_currency=master_currency,
        title="Portfolio performance since inception",
        sheet=summary_sheet,
    )
    plot_donut_chart(
        labels=portfolio_summary[PortfolioSummary.account.value].to_list()
        + cash_accounts_summary[CashAccountSummary.account.value].to_list(),
        sizes=portfolio_summary[PortfolioSummary.value.value].to_list()
        + cash_accounts_summary[CashAccountSummary.balance.value].to_list(),
        title="Asset Allocation",
        sheet=summary_sheet,
    )

    print("done")


if __name__ == "__main__":
    xw.Book("main.xlsm").set_mock_caller()
    main()
