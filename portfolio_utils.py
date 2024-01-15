import datetime as dt
from typing import Tuple

import numpy as np
import pandas as pd

from constant import YFinanceColumns, OrderColumns
from utils import get_historical_prices_with_dates


def compute_sharpe_ratio(historical_df) -> float:
    returns = historical_df[YFinanceColumns.price.value].diff()
    return np.sqrt(252) * returns.mean() / returns.std()


def compute_position_value_and_dividend_over_time(order_df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    start_date = order_df[OrderColumns.date.value].min()
    hist = get_historical_prices_with_dates(
        order_df[OrderColumns.sym.value].iloc[0],
        order_df[OrderColumns.market.value].iloc[0],
        start_date=start_date,
        end_date=dt.date.today(),
    ).reset_index()
    hist[YFinanceColumns.date.value] = hist[YFinanceColumns.date.value].dt.date

    order_df[OrderColumns.date.value] = order_df[OrderColumns.date.value].dt.date
    positions_change = order_df.set_index(OrderColumns.date.value)[OrderColumns.qty.value]

    dividends = hist.set_index(YFinanceColumns.date.value)[YFinanceColumns.dividends.value]
    capital_gain = hist.set_index(YFinanceColumns.date.value)[YFinanceColumns.price.value]

    positions = pd.Series(0, index=dividends.index)
    positions.loc[positions_change.index] = positions_change
    positions = positions.cumsum()

    dividends_earned = positions * dividends
    position_value = positions * capital_gain
    return position_value, dividends_earned
