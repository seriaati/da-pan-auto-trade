import json


def read_price_cache() -> dict[str, dict[str, float]]:
    try:
        with open("last_close_price.json", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_price_cache(last_close_price: dict[str, dict[str, float]]) -> None:
    with open("last_close_price.json", "w", encoding="utf-8") as f:
        json.dump(last_close_price, f)
