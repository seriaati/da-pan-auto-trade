from __future__ import annotations

import os

import shioaji as sj
import shioaji.constant as sjc


def setup_api(simulation: bool) -> sj.Shioaji:
    """Set up the API."""
    api = sj.Shioaji(simulation=simulation)
    api.login(api_key=os.environ["SHIOAJI_API_KEY"], secret_key=os.environ["SHIOAJI_SECRET_KEY"])
    api.activate_ca(
        ca_path=os.environ["SHIOAJI_CA_PATH"],
        ca_passwd=os.environ["SHIOAJI_CA_PASSWD"],
        person_id=os.environ["SHIOAJI_PERSON_ID"],
    )
    return api


def get_sell_price(api: sj.Shioaji) -> float:
    """取得元大台灣50正2委賣價"""
    contracts = [api.Contracts.Stocks["00631L"]]
    snapshots = api.snapshots(contracts)
    sell_price = snapshots[0].sell_price
    return sell_price


def get_buy_price(api: sj.Shioaji) -> float:
    """取得元大台灣50正2委買價"""
    contracts = [api.Contracts.Stocks["00631L"]]
    snapshots = api.snapshots(contracts)
    buy_price = snapshots[0].buy_price
    return buy_price


def is_stock_on_hand(api: sj.Shioaji) -> bool:
    """是否持有元大台灣50正2"""
    positions = api.list_positions(unit=sjc.Unit.Share)
    return any(position.code == "00631L" for position in positions)


def trade_stock(api: sj.Shioaji, action: sjc.Action, amount: int, price: float) -> None:
    """交易元大台灣50正2"""
    contract = api.Contracts.Stocks["00631L"]
    order = api.Order(
        action=action,
        price_type=sjc.StockPriceType.LMT,
        order_type=sjc.OrderType.ROD,
        order_lot=sjc.StockOrderLot.IntradayOdd,
        quantity=amount,
        price=price,
    )
    api.place_order(contract, order)


def buy_stock(api: sj.Shioaji, amount: int, price: float) -> None:
    """買入元大台灣50正2"""
    trade_stock(api, sjc.Action.Buy, amount, price)


def sell_stock(api: sj.Shioaji, amount: int, price: float) -> None:
    """賣出元大台灣50正2"""
    trade_stock(api, sjc.Action.Sell, amount, price)
