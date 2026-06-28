#!/usr/bin/env python3
"""Taiwan runtime sanity checks for PanWatch.

Default mode is offline and deterministic: validates the Taiwan news path using
PanWatch's safe configured-news collector. Pass ``--live-finmind`` to also make a
read-only FinMind request for TSMC/2330 using the configured FINMIND_TOKEN.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.collectors.news_collector import TaiwanConfiguredNewsCollector
from src.core.providers.base import ProviderRequest
from src.core.providers.quote.finmind import FinMindQuoteProvider


TSMC_SYMBOL = "2330"


def validate_tsmc_quote_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Assert that a quote payload is a Taiwan/FinMind EOD TSMC quote.

    This intentionally rejects payloads that silently treat 2330 as CN, CNY,
    lots-based volume, or real-time data. FinMind TaiwanStockPrice is daily/EOD.
    """
    assert payload.get("symbol") == TSMC_SYMBOL, "expected TSMC symbol 2330"
    assert payload.get("market") == "TW", "TSMC quote must be market=TW"
    assert payload.get("currency") == "TWD", "Taiwan quotes must use TWD"
    assert payload.get("quote_kind") == "eod", "FinMind TaiwanStockPrice is EOD, not realtime"
    assert payload.get("volume_unit") == "shares", "Taiwan FinMind volume must be normalized as shares"
    assert payload.get("provenance") == "finmind:TaiwanStockPrice"
    price = float(payload.get("current_price") or 0)
    assert price > 0, "TSMC price must be positive"
    as_of = str(payload.get("as_of") or "")
    assert as_of, "TSMC quote must expose as_of date"
    return {
        "symbol": TSMC_SYMBOL,
        "market": "TW",
        "price": price,
        "currency": "TWD",
        "quote_kind": "eod",
        "as_of": as_of,
    }


async def sanity_check_configured_taiwan_news(
    *,
    now: datetime | None = None,
    symbols: tuple[str, ...] = (TSMC_SYMBOL,),
) -> dict[str, Any]:
    """Verify the Taiwan news path returns a TSMC item without hitting CN sources.

    This uses the safe ``taiwan_configured`` collector. It proves PanWatch can
    carry Taiwan news items end-to-end once an approved source or manually
    curated item is configured, while avoiding unapproved scraping.
    """
    now = now or datetime.now()
    collector = TaiwanConfiguredNewsCollector(
        items=[
            {
                "external_id": "tw-sanity-2330",
                "title": "台積電法說會重點整理",
                "content": "此項目用於驗證 PanWatch 台股新聞路徑，不代表即時新聞。",
                "publish_time": now.isoformat(),
                "symbols": [TSMC_SYMBOL],
                "importance": 2,
                "url": "https://example.invalid/panwatch/tw-sanity-2330",
            }
        ]
    )
    items = await collector.fetch_news(list(symbols), now - timedelta(days=1))
    assert items, "expected configured Taiwan news item for TSMC"
    item = items[0]
    assert item.source == "taiwan_configured"
    assert TSMC_SYMBOL in item.symbols
    assert "台積電" in item.title
    return {
        "ok": True,
        "symbol": TSMC_SYMBOL,
        "source": item.source,
        "title": item.title,
        "importance": item.importance,
    }


async def sanity_check_live_finmind_tsmc() -> dict[str, Any]:
    """Make a read-only live FinMind TSMC quote request and validate semantics."""
    if not os.getenv("FINMIND_TOKEN"):
        raise RuntimeError("FINMIND_TOKEN is not set; cannot run live FinMind sanity check")
    response = await FinMindQuoteProvider().fetch(
        ProviderRequest(symbols=(TSMC_SYMBOL,), market="TW")
    )
    if not response.success or not response.data:
        raise RuntimeError(f"FinMind TSMC quote failed: {response.error or 'empty data'}")
    return validate_tsmc_quote_payload(response.data[0])


async def _main() -> int:
    parser = argparse.ArgumentParser(description="PanWatch Taiwan sanity checks")
    parser.add_argument("--live-finmind", action="store_true", help="call FinMind for live TSMC data")
    args = parser.parse_args()

    result: dict[str, Any] = {
        "configured_taiwan_news": await sanity_check_configured_taiwan_news(),
    }
    if args.live_finmind:
        result["live_finmind_tsmc"] = await sanity_check_live_finmind_tsmc()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
