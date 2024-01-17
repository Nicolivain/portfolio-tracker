import datetime as dt
from functools import lru_cache

import pandas as pd
import xlwings as xw
import yfinance as yf

from constant import MARKET_MAP


def read_table(origin: str, sheet: xw.Sheet, **kwargs) -> pd.DataFrame:
    df = sheet[origin].expand().options(pd.DataFrame, **kwargs).value
    return df


def save_dataframe(df: pd.DataFrame, origin: str, sheet: xw.Sheet, **kwargs):
    sheet[origin].expand().options(**kwargs).value = df


def positive_weighted_average(group: pd.DataFrame, data_col: str, weight_col: str) -> float:
    msk = group[weight_col] > 0
    return (group.loc[msk, data_col] * group.loc[msk, weight_col]).sum() / group.loc[msk, weight_col].sum()


def get_yfinance_sym(stock_sym: str, market_code: str) -> str:
    if stock_sym.endswith("."):
        stock_sym = stock_sym[:-1]
    tkr = f"{stock_sym}" + (f".{MARKET_MAP[market_code]}" if market_code in MARKET_MAP else "")
    return tkr


def get_company_info(stock_symbol, market_code):
    tkr = get_yfinance_sym(stock_symbol, market_code)
    ticker = yf.Ticker(tkr)
    company_name = ticker.info["longName"]
    local_currency = ticker.info["currency"]
    return company_name, local_currency


@lru_cache()
def get_today_forex_rates(base_currency: str, target_currency: str) -> pd.Series:
    today_str = dt.date.today().strftime("%Y-%m-%d")
    last_day_str = (dt.date.today() - dt.timedelta(days=5)).strftime("%Y-%m-%d")
    forex_pair = base_currency + target_currency + "=X"  # Append "=X" to the currency pair for Yahoo Finance
    forex_data = yf.download(forex_pair, start=last_day_str, end=today_str)
    return forex_data["Close"].iloc[-1]


@lru_cache()
def get_forex_rates_series(
    base_currency: str, target_currency: str, start_date: dt.date, end_date: dt.date
) -> pd.Series:
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    forex_pair = base_currency + target_currency + "=X"  # Append "=X" to the currency pair for Yahoo Finance
    forex_data = yf.download(forex_pair, start=start_str, end=end_str)
    return forex_data["Close"]


@lru_cache()
def get_historical_prices_with_dates(
    stock_symbol: str, market_code: str, start_date: dt.date, end_date: dt.date
) -> pd.DataFrame:
    tkr = get_yfinance_sym(stock_symbol, market_code)
    ticker = yf.Ticker(tkr)
    historical_data = ticker.history(start=start_date, end=end_date)
    return historical_data
