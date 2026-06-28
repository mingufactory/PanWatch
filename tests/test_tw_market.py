from datetime import datetime, timezone

from src.models.market import MARKETS, MarketCode
from src.core.context_builder import ContextBuilder


def test_tw_market_definition():
    market = MARKETS[MarketCode.TW]
    assert market.name == "台股"
    assert market.timezone == "Asia/Taipei"
    assert [(s.start.isoformat(), s.end.isoformat()) for s in market.sessions] == [
        ("09:00:00", "13:30:00")
    ]


def test_tw_regular_session_uses_taipei_time():
    market = MARKETS[MarketCode.TW]
    assert market.is_trading_time(datetime(2026, 6, 29, 1, 0, tzinfo=timezone.utc))
    assert market.is_trading_time(datetime(2026, 6, 29, 5, 30, tzinfo=timezone.utc))
    assert not market.is_trading_time(datetime(2026, 6, 29, 5, 31, tzinfo=timezone.utc))
    assert not market.is_trading_time(datetime(2026, 6, 28, 2, 0, tzinfo=timezone.utc))


def test_tw_benchmark_metadata_does_not_fall_back_to_cn():
    assert ContextBuilder._index_for_market(MarketCode.TW) == (
        "TAIEX",
        "臺灣加權指數",
    )
