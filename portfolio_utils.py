import datetime as dt
from typing import Tuple

import numpy as np
import pandas as pd

from constant import YFinanceColumns, OrderColumns
from utils import get_historical_prices_with_dates, get_company_info, get_forex_rates_series


def compute_sharpe_ratio(historical_df) -> float:
    returns = historical_df[YFinanceColumns.price.value].diff()
    return np.sqrt(252) * returns.mean() / returns.std()


def compute_position_value_and_dividend_over_time(asset_order_df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    start_date = asset_order_df[OrderColumns.date.value].min()
    hist = get_historical_prices_with_dates(
        asset_order_df[OrderColumns.sym.value].iloc[0],
        asset_order_df[OrderColumns.market.value].iloc[0],
        start_date=start_date,
        end_date=dt.date.today(),
    ).reset_index()
    hist[YFinanceColumns.date.value] = hist[YFinanceColumns.date.value].dt.date

    asset_order_df[OrderColumns.date.value] = asset_order_df[OrderColumns.date.value].dt.date
    positions_change = asset_order_df.set_index(OrderColumns.date.value)[OrderColumns.qty.value]

    dividends = hist.set_index(YFinanceColumns.date.value)[YFinanceColumns.dividends.value]
    capital_gain = hist.set_index(YFinanceColumns.date.value)[YFinanceColumns.price.value]

    positions = pd.Series(0, index=dividends.index)
    positions.loc[positions_change.index] = positions_change
    positions = positions.cumsum()

    dividends_earned = positions * dividends
    position_value = positions * capital_gain
    return position_value, dividends_earned


def compute_portfolio_returns_over_time(portfolio_oder_df: pd.DataFrame, book_currency: str):
    asset_orders = portfolio_oder_df.groupby(OrderColumns.sym.value)
    portfolio_positions_over_time = pd.DataFrame()
    asset_return_over_time = pd.DataFrame()
    end_date = dt.date.today()
    for asset_name, asset_order_df in asset_orders:
        position_value, _ = compute_position_value_and_dividend_over_time(asset_order_df)
        position_value = position_value.rename(asset_name)
        start_date = position_value.index.min()

        instrument_name, local_ccy = get_company_info(
            asset_order_df[OrderColumns.sym.value].iloc[0], asset_order_df[OrderColumns.market.value].iloc[0]
        )

        fx_rate = 1
        if local_ccy != book_currency:
            if local_ccy == "GBp" and book_currency == "GBP":
                # fx_rate = 1 / 100
                fx_rate /= 100

            elif local_ccy == "GBp":
                fx_rate = get_forex_rates_series("GBP", book_currency, start_date, end_date) / 100
            else:
                fx_rate = get_forex_rates_series(local_ccy, book_currency, start_date, end_date)

        position_value *= fx_rate

        asset_value = (
            get_historical_prices_with_dates(
                asset_name, asset_order_df[OrderColumns.market.value].iloc[0], start_date, end_date
            )
        ).reset_index()
        asset_value[YFinanceColumns.date.value] = asset_value[YFinanceColumns.date.value].dt.date
        asset_value = asset_value.set_index(YFinanceColumns.date.value)[YFinanceColumns.price.value]
        asset_value *= fx_rate

        portfolio_positions_over_time = pd.concat([portfolio_positions_over_time, position_value], axis=1)
        asset_return_over_time = pd.concat(
            [
                asset_return_over_time,
                asset_value.rename(asset_name),
            ],
            axis=1,
        )
    portfolio_positions_over_time = portfolio_positions_over_time.sort_index().ffill()
    asset_return_over_time = asset_return_over_time.sort_index().ffill().diff().shift(-1).fillna(0)
    portfolio_positions_over_time = portfolio_positions_over_time.fillna(0)

    # Normalize by total notional
    z = portfolio_positions_over_time.sum(axis=1)
    portfolio_weights_over_time = portfolio_positions_over_time.div(z.values, axis=0)

    portfolio_return_over_time = (
        portfolio_weights_over_time * asset_return_over_time.div(portfolio_positions_over_time).fillna(0)
    ).sum(axis=1)
    return portfolio_return_over_time


def compute_backtest_metrics(returns_time_series: pd.Series) -> Tuple:
    sharpe = np.sqrt(252) * returns_time_series.mean() / returns_time_series.std()
    vol = np.sqrt(252) * returns_time_series.std()

    cum_returns = (1 + returns_time_series).cumprod()
    peak = cum_returns.expanding(min_periods=1).max()
    drawdown = (cum_returns - peak) / peak
    return sharpe, vol, drawdown.min()
