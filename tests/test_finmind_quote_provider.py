import json
import asyncio
from pathlib import Path
import pytest
from src.core.providers.base import ProviderRequest
from src.core.providers.quote.finmind import FinMindQuoteProvider

class StubClient:
    async def fetch(self, dataset, data_id, **kwargs):
        path = Path(__file__).parent / "fixtures" / "finmind" / f"taiwan_stock_price_{data_id}.json"
        return json.loads(path.read_text())["data"]

def test_quote_is_explicitly_eod_with_provenance():
    response = asyncio.run(FinMindQuoteProvider(client=StubClient()).fetch(ProviderRequest(symbols=("2330", "0050"), market="TW")))
    assert response.success and len(response.data) == 2
    quote = response.data[0]
    assert quote["current_price"] == 1075 and quote["quote_kind"] == "eod"
    assert quote["as_of"] == "2026-06-25" and quote["provenance"] == "finmind:TaiwanStockPrice"

def test_quote_rejects_non_tw():
    response = asyncio.run(FinMindQuoteProvider(client=StubClient()).fetch(ProviderRequest(symbols=("2330",), market="CN")))
    assert not response.success
