from __future__ import annotations

import asyncio
from datetime import datetime

from scripts.tw_sanity_check import (
    sanity_check_configured_taiwan_news,
    validate_tsmc_quote_payload,
)


def test_tsmc_quote_payload_validator_requires_taiwan_eod_fields() -> None:
    payload = {
        "symbol": "2330",
        "market": "TW",
        "current_price": 1075.0,
        "prev_close": 1060.0,
        "as_of": "2026-06-25",
        "quote_kind": "eod",
        "currency": "TWD",
        "volume_unit": "shares",
        "provenance": "finmind:TaiwanStockPrice",
    }

    assert validate_tsmc_quote_payload(payload) == {
        "symbol": "2330",
        "market": "TW",
        "price": 1075.0,
        "currency": "TWD",
        "quote_kind": "eod",
        "as_of": "2026-06-25",
    }


def test_tsmc_quote_payload_validator_rejects_non_taiwan_or_realtime_claims() -> None:
    bad = {
        "symbol": "2330",
        "market": "CN",
        "current_price": 1075.0,
        "as_of": "2026-06-25",
        "quote_kind": "realtime",
        "currency": "CNY",
        "volume_unit": "lots",
        "provenance": "finmind:TaiwanStockPrice",
    }

    try:
        validate_tsmc_quote_payload(bad)
    except AssertionError as exc:
        assert "TW" in str(exc) or "eod" in str(exc)
    else:
        raise AssertionError("non-TW/realtime TSMC payload should fail sanity validation")


def test_configured_taiwan_news_sanity_gets_tsmc_item_without_network() -> None:
    result = asyncio.run(
        sanity_check_configured_taiwan_news(
            now=datetime(2026, 6, 25, 10, 0, 0),
            symbols=("2330",),
        )
    )

    assert result["ok"] is True
    assert result["symbol"] == "2330"
    assert result["source"] == "taiwan_configured"
    assert "台積電" in result["title"]
