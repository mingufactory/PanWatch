import json
import asyncio
from pathlib import Path
import httpx
import pytest
from src.core.providers.finmind_client import FinMindClient, FinMindError, normalize_price_rows

FIXTURES = Path(__file__).parent / "fixtures" / "finmind"

def fixture(name): return json.loads((FIXTURES / name).read_text())

def test_client_success_and_config_token_precedence(monkeypatch):
    monkeypatch.setenv("FINMIND_TOKEN", "env-token")
    seen = {}
    async def handler(request):
        seen.update(dict(request.url.params)); return httpx.Response(200, json=fixture("taiwan_stock_price_2330.json"))
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            return await FinMindClient({"token": "config-token"}, client=http).fetch("TaiwanStockPrice", "2330")
    rows = asyncio.run(run())
    assert len(rows) == 2 and seen["token"] == "config-token"

def test_client_redacts_token_from_api_error():
    token = "sanitized-example-token"
    async def handler(request): return httpx.Response(200, json=fixture("error_rate_limit.json"))
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            return await FinMindClient({"token": token}, client=http).fetch("TaiwanStockPrice", "2330")
    with pytest.raises(FinMindError) as error:
        asyncio.run(run())
    assert token not in str(error.value) and "[REDACTED]" in str(error.value)

def test_normalizer_sorts_deduplicates_and_drops_malformed():
    rows = fixture("taiwan_stock_price_2330.json")["data"]
    result = normalize_price_rows([rows[1], {**rows[0], "close": None}, rows[0], rows[1]], "2330")
    assert [row["date"] for row in result] == ["2026-06-24", "2026-06-25"]
