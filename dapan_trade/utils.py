import os

import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger


def get_stock_ids() -> list[str]:
    """Get 4 digit stock IDs from the API."""
    stocks: list[dict[str, str]] = requests.get("https://stock-api.seriaati.xyz/stocks").json()
    return [stock["id"] for stock in stocks if len(stock["id"]) == 4]


def get_stock_last_close_prices(stock_id: str) -> dict[str, float]:
    """Get the last 120 days of close prices for a stock."""
    stocks = requests.get(
        f"https://stock-api.seriaati.xyz/history_trades/{stock_id}?limit=120"
    ).json()
    if stocks:
        return {stock["date"]: stock["close_price"] for stock in stocks}
    return {}


def convert_to_multiindex_df(
    data: dict[str, dict[str, float]],
) -> pd.DataFrame:
    """Convert the data to a multi-index DataFrame."""
    # Prepare data for DataFrame
    df = pd.DataFrame(
        [
            (date, stock_id, price)
            for stock_id, dates in data.items()
            for date, price in dates.items()
        ],
        columns=["Date", "Stock ID", "Price"],
    )

    # Set multi-index
    df.set_index(["Date", "Stock ID"], inplace=True)
    df = df.unstack(level="Stock ID")

    # Remove the 'Price' level from column labels
    df.columns = df.columns.droplevel(0)

    # Sort the index and columns
    df.sort_index(inplace=True)

    return df  # pyright: ignore [reportReturnType]


def is_holdable(df: pd.DataFrame) -> bool:
    """判斷能不能持有元大台灣50正2"""
    rise_cnt = (df.pct_change() > 0).sum(axis=1)
    fall_cnt = (df.pct_change() < 0).sum(axis=1)

    ind = (rise_cnt / (rise_cnt + fall_cnt)) - 0.5

    ind_s = ind.rolling(20).mean()[-1]
    ind_l = ind.rolling(120).mean()[-1]

    return ind_s > ind_l


def is_market_closed() -> bool:
    """Check if the market is closed."""
    base = "https://tw.stock.yahoo.com/quote/2330.TW"
    req = requests.get(base)
    allsoup = BeautifulSoup(req.content, "html.parser")
    status = allsoup.find("span", {"class": "C(#6e7780) Fz(12px) Fw(b)"}).text[0:2]  # pyright: ignore[reportOptionalMemberAccess]
    return status == "收盤"


def check_env() -> None:
    """Check if the necessary environment variables are set."""
    envs_to_check = (
        "SHIOAJI_API_KEY",
        "SHIOAJI_SECRET_KEY",
        "SHIOAJI_PERSON_ID",
        "SHIOAJI_CA_PATH",
        "SHIOAJI_CA_PASSWD",
        "LINE_NOTIFY_TOKEN",
    )
    for env in envs_to_check:
        if env not in os.environ:
            msg = f"Environment variable {env} is not set."
            raise RuntimeError(msg)


def line_notify(message: str, *, exc_info: bool = False) -> None:
    """Send a message to LINE Notify (and log to console at the same time)."""
    if exc_info:
        logger.exception(message)
    else:
        logger.info(message)

    url = "https://notify-api.line.me/api/notify"
    token = os.environ["LINE_NOTIFY_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": message}
    requests.post(url, headers=headers, data=data)
