import pytest
import sys
sys.path.append(".")
from src.shop import Shop

def test_normal_shop_purchase():
    shop = Shop(5,10,0)
    shop.buy_item()
    shop.buy_item()

    item_price = shop.get_item_price()
    assert shop.get_items() == 8
    assert shop.get_money() == item_price * 2

def test_normal_shop_purchase2():
    shop = Shop(5,10,0)
    shop.buy_item()
    shop.buy_item()
    shop.buy_item()
    shop.buy_item()

    item_price = shop.get_item_price()

    assert shop.get_items() == 6
    assert shop.get_money() == item_price * 4

def test_empty_shop_purchase():
    shop = Shop(5,0,0)
    shop.buy_item()
    assert shop.get_money() == 0

	


