import asyncio
from datetime import datetime, timedelta

from src.collectors.news_collector import (
    EastMoneyNewsCollector,
    EastMoneyStockNewsCollector,
    NewsCollector,
    TaiwanConfiguredNewsCollector,
)


def test_tw_symbols_do_not_fall_through_to_eastmoney_collectors(monkeypatch):
    calls = []

    async def fake_fetch(self, symbols=None, since=None):
        calls.append((self.source, tuple(symbols or ())))
        raise AssertionError("TW symbols must not use China news collectors")

    monkeypatch.setattr(EastMoneyStockNewsCollector, "fetch_news", fake_fetch)
    monkeypatch.setattr(EastMoneyNewsCollector, "fetch_news", fake_fetch)

    collector = NewsCollector(
        collectors=[EastMoneyStockNewsCollector(), EastMoneyNewsCollector()]
    )
    result = asyncio.run(
        collector.fetch_all(
            symbols=["2330", "0050"],
            since_hours=24,
            symbol_names={"2330": "台積電", "0050": "元大台灣50"},
            symbol_markets={"2330": "TW", "0050": "TW"},
        )
    )
    assert result == []
    assert calls == []


def test_taiwan_configured_news_returns_only_matching_symbols():
    collector = TaiwanConfiguredNewsCollector(
        items=[
            {
                "external_id": "tw-1",
                "title": "台積電法說會重點",
                "content": "AI 需求與資本支出展望。",
                "publish_time": datetime.now().isoformat(),
                "symbols": ["2330"],
                "importance": 2,
                "url": "https://example.invalid/tw-1",
            },
            {
                "external_id": "tw-2",
                "title": "鴻海公告",
                "publish_time": datetime.now().isoformat(),
                "symbols": ["2317"],
            },
        ]
    )
    result = asyncio.run(collector.fetch_news(["2330"], datetime.now() - timedelta(days=1)))
    assert len(result) == 1
    assert result[0].source == "taiwan_configured"
    assert result[0].symbols == ["2330"]


def test_mixed_market_news_routes_by_explicit_market(monkeypatch):
    calls = []

    async def fake_fetch(self, symbols=None, since=None):
        calls.append((self.source, tuple(symbols or ())))
        return []

    monkeypatch.setattr(EastMoneyStockNewsCollector, "fetch_news", fake_fetch)
    monkeypatch.setattr(EastMoneyNewsCollector, "fetch_news", fake_fetch)

    collector = NewsCollector(
        collectors=[EastMoneyStockNewsCollector(), EastMoneyNewsCollector()]
    )
    asyncio.run(
        collector.fetch_all(
            symbols=["2330", "600519"],
            since_hours=24,
            symbol_names={"2330": "台積電", "600519": "贵州茅台"},
            symbol_markets={"2330": "TW", "600519": "CN"},
        )
    )
    assert calls == [("eastmoney_news", ("600519",)), ("eastmoney", ("600519",))]
