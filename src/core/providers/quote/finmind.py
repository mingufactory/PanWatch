from __future__ import annotations

from datetime import date, timedelta

from src.core.providers.base import ProviderRequest, ProviderResponse, QuoteProvider
from src.core.providers.finmind_client import (
    FinMindClient,
    FinMindError,
    normalize_price_rows,
)


class FinMindQuoteProvider(QuoteProvider):
    """EOD projection from TaiwanStockPrice; never a real-time quote."""

    name = "finmind"
    supports_markets = {"TW"}

    def __init__(
        self, config: dict | None = None, *, client: FinMindClient | None = None
    ):
        super().__init__(config)
        self.client = client or FinMindClient(self.config)

    async def fetch(self, req: ProviderRequest) -> ProviderResponse:
        if req.market != "TW":
            return ProviderResponse(
                success=False, error=f"FinMind only supports TW, got {req.market}"
            )

        end = date.today()
        start = end - timedelta(days=14)
        quotes = []
        try:
            for symbol in req.symbols:
                raw = await self.client.fetch(
                    "TaiwanStockPrice",
                    symbol,
                    start_date=start.isoformat(),
                    end_date=end.isoformat(),
                )
                rows = normalize_price_rows(raw, symbol)
                if not rows:
                    continue
                current = rows[-1]
                previous = rows[-2]["close"] if len(rows) > 1 else None
                change = (
                    current["close"] - previous
                    if previous not in (None, 0)
                    else None
                )
                quotes.append(
                    {
                        "symbol": symbol,
                        "market": "TW",
                        "current_price": current["close"],
                        "prev_close": previous,
                        "change_amount": change,
                        "change_pct": change / previous * 100 if change is not None else None,
                        "open_price": current["open"],
                        "high_price": current["high"],
                        "low_price": current["low"],
                        "volume": current["volume"],
                        "turnover": current["turnover"],
                        "provenance": "finmind:TaiwanStockPrice",
                        "as_of": current["date"],
                        "quote_kind": "eod",
                        "currency": "TWD",
                        "volume_unit": "shares",
                        "adjustment": "unadjusted",
                    }
                )
        except FinMindError as exc:
            return ProviderResponse(success=False, error=str(exc))
        return ProviderResponse(
            success=True,
            data=quotes,
            partial=bool(quotes) and len(quotes) < len(req.symbols),
        )
