import datetime as dt
import matplotlib
import pandas as pd
import xlwings as xw

from typing import Dict

from portfolio_tracker.constant import (
    OrderColumns,
    MovementColumns,
    PortfolioColumns,
    CashAccountSummary,
    PortfolioSummary,
    PORTFOLIO_DISPLAY_ORDER,
)
from portfolio_tracker.budget_utils import (
    preprocess_budget_data,
    get_income,
    get_expenses,
    plot_income_category,
    plot_expenses_category,
    update_budget,
)

from portfolio_tracker.utils import (
    read_table,
    save_dataframe,
)

from portfolio_tracker.core import (
    compute_signed_quantity,
    aggregate_orders_to_portfolio_df,
    build_cash_accounts_summary,
    build_portfolio_analytics,
    build_portfolio_summary,
)
from portfolio_tracker.plot import plot_donut_chart, plot_portfolio_returns

matplotlib.use("Agg")


def main(book_currencies: Dict[str, str], reporting_currency: str = "EUR"):
    wb = xw.Book.caller()
    mvt_sheet = wb.sheets["Mouvements"]
    order_sheet = wb.sheets["Ordres"]
    summary_sheet = wb.sheets["Investissement"]
    budget_sheet = wb.sheets["Budget"]

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
        book_ccy = book_currencies.get(portfolio_key, reporting_currency)
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
        mvt_data, order_data, portfolios, book_currencies, reporting_currency
    )
    save_dataframe(cash_accounts_summary, "B8", summary_sheet, index=False)
    portfolio_summary = build_portfolio_summary(order_data, portfolios, book_currencies, reporting_currency)
    save_dataframe(portfolio_summary, "B20", summary_sheet, index=False)

    plot_portfolio_returns(
        portfolio_order_df=order_data,
        start_date=pd.to_datetime(dt.date.today() - dt.timedelta(days=365)),
        book_currency=reporting_currency,
        title="Portfolio performance 1Y",
        sheet=summary_sheet,
    )
    plot_portfolio_returns(
        portfolio_order_df=order_data,
        start_date=order_data[OrderColumns.date.value].min(),
        book_currency=reporting_currency,
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

    # Budget sheet
    budget_sheet.range("A1").value = (
        "To import a bank account history, either paste your history starting from B2 cell and specify headers in constant.py, or go to Developer > Insert > Button, and link the button to the import_csv() function in budget_utils.py "
    )
    budget_history_df = read_table("B2", budget_sheet, index=0, header=1).reset_index()
    if not budget_history_df.empty:
        budget_history_df = preprocess_budget_data(budget_history_df)
        update_budget()

        # Add the dropdown menu to cell O2
        cell = budget_sheet.range("O2").api
        options = "All time, Last 30 days, Last 90 days, Last 180 days, Last 365 days, Year to date"
        cell.Validation.Delete()
        cell.Validation.Add(Type=3, AlertStyle=2, Operator=1, Formula1=options)
        cell.Validation.IgnoreBlank = True
        cell.Validation.InCellDropdown = True

        income = get_income(budget_history_df)
        expenses = get_expenses(budget_history_df)

        plot_income_category(income, budget_sheet)
        plot_income_category(income, budget_sheet, subcategory=True)
        plot_expenses_category(expenses, budget_sheet)
        plot_expenses_category(expenses, budget_sheet, subcategory=True)

    print("Done")
