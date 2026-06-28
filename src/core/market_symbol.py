"""Market-aware canonical symbol normalization and validation."""

from __future__ import annotations

import re

from src.models.market import MARKETS, MarketCode


def parse_market(market: MarketCode | str) -> MarketCode:
    """Return a validated market code without silently choosing a default."""
    if isinstance(market, MarketCode):
        return market
    try:
        return MarketCode(str(market).strip().upper())
    except ValueError as exc:
        raise ValueError(f"unsupported market: {market}") from exc


def normalize_symbol(symbol: str, market: MarketCode | str) -> str:
    """Normalize a user/vendor symbol to its canonical unsuffixed form."""
    market_code = parse_market(market)
    value = str(symbol or "").strip().upper()
    suffixes = {
        MarketCode.TW: (".TW", ".TWO"),
        MarketCode.CN: (".SH", ".SZ", ".BJ"),
        MarketCode.HK: (".HK",),
    }
    for suffix in suffixes.get(market_code, ()):
        if value.endswith(suffix):
            value = value[: -len(suffix)]
            break
    if market_code == MarketCode.CN and len(value) == 8 and value[:2] in {"SH", "SZ", "BJ"}:
        value = value[2:]
    return value


def validate_symbol(symbol: str, market: MarketCode | str) -> bool:
    """Validate canonical syntax; exchange security masters may be stricter."""
    market_code = parse_market(market)
    return re.fullmatch(MARKETS[market_code].symbol_pattern, normalize_symbol(symbol, market_code)) is not None


def normalize_tw_symbol(symbol: str) -> str:
    return normalize_symbol(symbol, MarketCode.TW)


def is_tw_symbol(symbol: str) -> bool:
    return validate_symbol(symbol, MarketCode.TW)


def to_yahoo_symbol(symbol: str, exchange: str = "TWSE") -> str:
    """Format a Taiwan symbol for Yahoo (.TW for TWSE, .TWO for TPEx)."""
    canonical = normalize_tw_symbol(symbol)
    if not is_tw_symbol(canonical):
        raise ValueError(f"invalid Taiwan symbol: {symbol}")
    board = exchange.strip().upper()
    if board == "TWSE":
        return f"{canonical}.TW"
    if board in {"TPEX", "OTC"}:
        return f"{canonical}.TWO"
    raise ValueError(f"unsupported Taiwan exchange: {exchange}")
