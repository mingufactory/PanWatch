"""Shared asynchronous client and normalizers for FinMind datasets."""
from __future__ import annotations
import os
from typing import Any
import httpx


class FinMindError(RuntimeError):
    pass


def _redact(value: str, token: str) -> str:
    return value.replace(token, "[REDACTED]") if token else value


def _number(value: Any) -> float | None:
    if value in (None, "", "null", "None"):
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


class FinMindClient:
    base_url = "https://api.finmindtrade.com/api/v4/data"

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config or {}
        self.token = str(self.config.get("token") or os.getenv("FINMIND_TOKEN") or "")
        self._client = client
        self.timeout = float(self.config.get("timeout", 10))

    async def fetch(
        self,
        dataset: str,
        data_id: str,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"dataset": dataset, "data_id": data_id}
        if self.token:
            params["token"] = self.token
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        own_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self.timeout)
        rows: list[dict[str, Any]] = []
        try:
            while True:
                try:
                    response = await client.get(self.base_url, params=params)
                    response.raise_for_status()
                    payload = response.json()
                except (httpx.HTTPError, ValueError) as exc:
                    message = _redact(f"FinMind request failed: {exc}", self.token)
                    raise FinMindError(message) from None
                if not isinstance(payload, dict):
                    raise FinMindError("FinMind malformed response")
                status = payload.get("status", 200)
                if status not in (200, "200", None):
                    message = _redact(str(payload.get("msg") or "unknown error"), self.token)
                    raise FinMindError(f"FinMind error status={status}: {message}")
                page = payload.get("data")
                if not isinstance(page, list):
                    raise FinMindError("FinMind malformed response: data is not a list")
                rows.extend(item for item in page if isinstance(item, dict))
                cursor = payload.get("next_cursor")
                next_page = payload.get("next_page")
                if cursor:
                    params["cursor"] = cursor
                elif next_page:
                    params["page"] = next_page
                else:
                    break
            return rows
        finally:
            if own_client:
                await client.aclose()


def normalize_price_rows(
    rows: list[dict[str, Any]], symbol: str
) -> list[dict[str, Any]]:
    by_date: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_symbol = str(row.get("stock_id") or row.get("data_id") or symbol)
        day = str(row.get("date") or "")
        open_, high = _number(row.get("open")), _number(row.get("max", row.get("high")))
        low, close = _number(row.get("min", row.get("low"))), _number(row.get("close"))
        volume = _number(row.get("Trading_Volume", row.get("volume")))
        if row_symbol != symbol or not day or None in (
            open_, high, low, close, volume
        ):
            continue
        if min(open_, high, low, close) < 0 or high < low:
            continue
        by_date[day] = {
            "symbol": symbol,
            "date": day,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "turnover": _number(row.get("Trading_money")),
        }
    return [by_date[key] for key in sorted(by_date)]
