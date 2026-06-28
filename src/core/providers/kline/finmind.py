from __future__ import annotations

from datetime import date, timedelta

from src.collectors.kline_collector import KlineData
from src.core.providers.base import KlineProvider, ProviderRequest, ProviderResponse
from src.core.providers.finmind_client import (
    FinMindClient,
    FinMindError,
    normalize_price_rows,
)


class FinMindKlineProvider(KlineProvider):
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
        if len(req.symbols) != 1:
            return ProviderResponse(
                success=False, error="FinMind kline requires one symbol"
            )

        days = next((int(value) for key, value in req.extra if key == "days"), 60)
        end = date.today()
        start = end - timedelta(days=max(days * 2, 30))
        try:
            raw = await self.client.fetch(
                "TaiwanStockPrice",
                req.symbols[0],
                start_date=start.isoformat(),
                end_date=end.isoformat(),
            )
        except FinMindError as exc:
            return ProviderResponse(success=False, error=str(exc))

        rows = normalize_price_rows(raw, req.symbols[0])[-max(1, days) :]
        data = [
            KlineData(
                date=row["date"],
                open=row["open"],
                close=row["close"],
                high=row["high"],
                low=row["low"],
                volume=row["volume"],
                provenance="finmind:TaiwanStockPrice",
                as_of=row["date"],
                quote_kind="eod",
                currency="TWD",
                volume_unit="shares",
                adjustment="unadjusted",
            )
            for row in rows
        ]
        return ProviderResponse(success=True, data=data)
