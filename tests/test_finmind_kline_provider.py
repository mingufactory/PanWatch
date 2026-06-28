import json
import asyncio
from pathlib import Path
import pytest
from src.core.providers.base import ProviderRequest
from src.core.providers.kline.finmind import FinMindKlineProvider

class StubClient:
    async def fetch(self, dataset, data_id, **kwargs):
        path = Path(__file__).parent / "fixtures" / "finmind" / f"taiwan_stock_price_{data_id}.json"
        return json.loads(path.read_text())["data"]

def test_kline_normalizes_daily_eod_bars():
    response = asyncio.run(FinMindKlineProvider(client=StubClient()).fetch(ProviderRequest(symbols=("2330",), market="TW", extra=(("days", 1),))))
    assert response.success and len(response.data) == 1
    bar = response.data[0]
    assert (bar.date, bar.close, bar.volume) == ("2026-06-25", 1075, 24321098)
    assert bar.quote_kind == "eod" and bar.volume_unit == "shares"
