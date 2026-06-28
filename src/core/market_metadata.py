"""Market trading metadata and conservative quote-freshness helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.models.market import MARKETS, MarketCode, MarketDef


def market_metadata(market: MarketCode | str) -> MarketDef:
    code = market if isinstance(market, MarketCode) else MarketCode(str(market).upper())
    return MARKETS[code]


def market_currency(market: MarketCode | str) -> str:
    return market_metadata(market).currency


def default_lot_size(market: MarketCode | str) -> int:
    return market_metadata(market).board_lot_size


def supports_capability(market: MarketCode | str, capability: str) -> bool:
    return capability in market_metadata(market).capabilities


def quote_kind(quote: dict[str, Any] | None) -> str:
    return str((quote or {}).get("quote_kind") or "unknown").strip().lower()


def quote_is_stale(
    quote: dict[str, Any] | None,
    market: MarketCode | str,
    *,
    now: datetime | None = None,
) -> bool:
    if not quote:
        return True
    if quote.get("is_stale") is True or quote.get("stale") is True:
        return True
    raw = quote.get("as_of")
    if not raw:
        return False
    try:
        as_of = raw if isinstance(raw, datetime) else datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=timezone.utc)
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        return (current.astimezone(timezone.utc) - as_of.astimezone(timezone.utc)).total_seconds() > market_metadata(market).quote_freshness_seconds
    except (TypeError, ValueError):
        return True


def quote_supports_price_alert(quote: dict[str, Any] | None, market: MarketCode | str) -> bool:
    code = market if isinstance(market, MarketCode) else MarketCode(str(market).upper())
    if not supports_capability(code, "price_alert"):
        return False
    if code == MarketCode.TW and quote_kind(quote) != "realtime":
        return False
    return not quote_is_stale(quote, code)


def position_valuation(*, price: float, cost_price: float, quantity: int) -> dict[str, float]:
    """Value one position in its native currency; no implicit FX conversion."""
    market_value = float(price) * int(quantity)
    cost = float(cost_price) * int(quantity)
    pnl = market_value - cost
    return {
        "market_value": market_value,
        "cost": cost,
        "pnl": pnl,
        "pnl_pct": (pnl / cost * 100.0) if cost > 0 else 0.0,
    }
