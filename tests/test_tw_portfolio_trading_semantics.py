from datetime import datetime, timedelta, timezone

from src.agents.tradingagents.toolkit_adapter import (
    is_a_share,
    is_panwatch_routable,
    is_tw_share,
    panwatch_data_context,
)
from src.core.market_metadata import (
    default_lot_size,
    market_currency,
    position_valuation,
    quote_supports_price_alert,
    supports_capability,
)
from src.models.market import MarketCode
from fastapi import HTTPException
from src.web.api.discovery import _require_discovery


class _Stock:
    symbol = "006208"
    name = "富邦台50"
    market = MarketCode.TW


def test_tw_metadata_lot_and_unsupported_cn_capabilities():
    assert market_currency("TW") == "TWD"
    assert default_lot_size("TW") == 1000
    assert not supports_capability("TW", "capital_flow")
    assert not supports_capability("TW", "events")
    assert not supports_capability("TW", "discovery")


def test_tw_portfolio_valuation_stays_native_twd():
    value = position_valuation(price=620.0, cost_price=600.0, quantity=1000)
    assert value == {
        "market_value": 620_000.0,
        "cost": 600_000.0,
        "pnl": 20_000.0,
        "pnl_pct": 20_000 / 600_000 * 100,
    }


def test_tw_alert_requires_fresh_explicit_realtime_quote():
    now = datetime.now(timezone.utc)
    assert not quote_supports_price_alert({"quote_kind": "eod", "as_of": now.isoformat()}, "TW")
    assert not quote_supports_price_alert({"quote_kind": "delayed", "as_of": now.isoformat()}, "TW")
    assert not quote_supports_price_alert(
        {"quote_kind": "realtime", "as_of": (now - timedelta(minutes=10)).isoformat()},
        "TW",
    )
    assert quote_supports_price_alert(
        {"quote_kind": "realtime", "as_of": now.isoformat()}, "TW"
    )


def test_numeric_tw_symbol_uses_explicit_market_not_a_share_route():
    # Shape alone remains ambiguous for compatibility; request context is authoritative.
    assert is_a_share("006208")
    with panwatch_data_context({"stock": _Stock()}):
        assert is_tw_share("006208")
        assert is_panwatch_routable("006208")


def test_tw_discovery_is_explicitly_unsupported():
    try:
        _require_discovery("TW")
    except HTTPException as exc:
        assert exc.status_code == 501
    else:
        raise AssertionError("TW must not fall through to EastMoney discovery")
