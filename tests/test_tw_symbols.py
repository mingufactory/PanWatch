import pytest

from src.core.cn_symbol import get_cn_exchange, get_cn_prefix, is_cn_sh
from src.core.market_symbol import (
    is_tw_symbol,
    normalize_symbol,
    normalize_tw_symbol,
    parse_market,
    to_yahoo_symbol,
)


@pytest.mark.parametrize("symbol", ["2330", "0050", "006208", "12345"])
def test_tw_symbol_lengths_remain_strings_and_unambiguous(symbol):
    assert normalize_tw_symbol(symbol) == symbol
    assert is_tw_symbol(symbol)


def test_tw_vendor_suffix_normalization_and_formatting():
    assert normalize_tw_symbol(" 2330.tw ") == "2330"
    assert normalize_tw_symbol("8069.TWO") == "8069"
    assert to_yahoo_symbol("2330", "TWSE") == "2330.TW"
    assert to_yahoo_symbol("8069", "TPEx") == "8069.TWO"


def test_market_is_required_for_numeric_symbol_identity():
    assert normalize_symbol("0050", "TW") == "0050"
    assert normalize_symbol("0050", "HK") == "0050"
    with pytest.raises(ValueError, match="unsupported market"):
        parse_market("XX")


def test_cn_symbol_compatibility():
    assert get_cn_exchange("600519") == "SH"
    assert get_cn_prefix("000738") == "sz"
    assert is_cn_sh("600519")
