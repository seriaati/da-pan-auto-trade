import argparse
import datetime
import time
import warnings

import pandas as pd
from dotenv import load_dotenv

from dapan_trade.cache import read_price_cache, save_price_cache
from dapan_trade.trade import (
    buy_stock,
    get_buy_price,
    get_sell_price,
    is_stock_on_hand,
    sell_stock,
    setup_api,
)
from dapan_trade.utils import (
    check_env,
    convert_to_multiindex_df,
    get_stock_ids,
    get_stock_last_close_prices,
    is_holdable,
    line_notify,
)

load_dotenv()

pd.set_option("mode.chained_assignment", None)
warnings.simplefilter(action="ignore", category=FutureWarning)


parser = argparse.ArgumentParser(description="Determine if the stocks are holdable.")
parser.add_argument("--no-cache", action="store_true", help="Ignore the cache.", default=False)
parser.add_argument("--no-simul", action="store_true", help="Ignore the simulation.", default=False)
parser.add_argument("--trade-amount", type=int, help="The amount of 零股 to trade.", default=0)

args = parser.parse_args()


def main() -> None:  # noqa: C901, PLR0912, PLR0915
    if datetime.datetime.now().weekday() >= 5:
        line_notify("今天是假日, 不執行")
        return

    check_env()
    line_notify(
        f"參數: 不使用快取 {args.no_cache}, 禁用測試模式 {args.no_simul}, 購買股數 {args.trade_amount}"
    )

    try:
        stock_ids = get_stock_ids()
    except Exception:
        line_notify("取得股票代碼失敗", exc_info=True)
        return

    line_notify(f"找到 {len(stock_ids)} 支股票")
    line_notify("開始取得所有股票的收盤價")

    stock_prices = {} if args.no_cache else read_price_cache()

    for stock_id in stock_ids:
        if stock_id in stock_prices:
            continue
        try:
            last_close_prices = get_stock_last_close_prices(stock_id)
        except Exception:
            line_notify(f"取得 {stock_id} 的收盤價失敗", exc_info=True)
            continue
        stock_prices[stock_id] = last_close_prices

    if not args.no_cache:
        save_price_cache(stock_prices)

    line_notify("成功取得所有股票的收盤價")

    df = convert_to_multiindex_df(stock_prices)
    is_hold = is_holdable(df)
    if is_hold:
        line_notify("元大台灣50正2, 可持有")
    else:
        line_notify("元大台灣50正2, 不可持有")

    try:
        api = setup_api(not args.no_simul)
    except Exception:
        line_notify("永豐金 API 登入失敗", exc_info=True)
        return

    try:
        is_on_hand = is_stock_on_hand(api)
    except Exception:
        line_notify("取得持有狀態失敗", exc_info=True)
        return

    if is_hold:
        if is_on_hand:
            line_notify("庫存有, 不買")
        else:
            line_notify("庫存沒有, 買進")

            try:
                sell_price = get_sell_price(api)
            except Exception:
                line_notify("取得委賣價失敗", exc_info=True)
                return

            try:
                buy_stock(api, args.trade_amount, sell_price)
            except Exception:
                line_notify("買進下單失敗", exc_info=True)
            else:
                line_notify(f"買進下單成功, 買價 {sell_price}, 股數 {args.trade_amount}")

    else:  # noqa: PLR5501
        if not is_on_hand:
            line_notify("庫存沒有, 沒得賣")
        else:
            line_notify("庫存有, 賣出")

            try:
                buy_price = get_buy_price(api)
            except Exception:
                line_notify("取得委買價失敗", exc_info=True)
                return

            try:
                sell_stock(api, args.trade_amount, buy_price)
            except Exception:
                line_notify("賣出下單失敗", exc_info=True)
            else:
                line_notify(f"賣出下單成功, 賣價 {buy_price}, 股數 {args.trade_amount}")


if __name__ == "__main__":
    line_notify("開始執行")

    start = time.time()
    try:
        main()
    except Exception:
        line_notify("執行失敗", exc_info=True)

    end = time.time()
    line_notify(f"執行結束, 花費 {end - start:.2f} 秒")
