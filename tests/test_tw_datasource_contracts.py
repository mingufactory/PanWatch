from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _seed_sources() -> list[dict]:
    tree = ast.parse((ROOT / "server.py").read_text(encoding="utf-8"))
    seed_fn = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "seed_data_sources"
    )
    assign = next(
        node
        for node in ast.walk(seed_fn)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "sources" for t in node.targets)
    )
    return ast.literal_eval(assign.value)


def _by_provider_type() -> dict[tuple[str, str], dict]:
    return {(row["type"], row["provider"]): row for row in _seed_sources()}


def test_fresh_install_seeds_finmind_as_primary_tw_quote_and_kline_source() -> None:
    rows = _by_provider_type()

    quote = rows[("quote", "finmind")]
    assert quote["enabled"] is True
    assert quote["priority"] == 0
    assert quote["config"]["market"] == "TW"
    assert quote["test_symbols"] == ["2330", "0050"]
    assert "EOD" in quote["config"]["description"] or "非即時" in quote["config"]["description"]

    kline = rows[("kline", "finmind")]
    assert kline["enabled"] is True
    assert kline["priority"] == 0
    assert kline["config"]["market"] == "TW"
    assert kline["test_symbols"] == ["2330", "0050"]


def test_fresh_install_seeds_safe_taiwan_news_source_before_china_sources() -> None:
    sources = _seed_sources()
    news_sources = [row for row in sources if row["type"] == "news"]

    assert news_sources[0]["provider"] == "taiwan_configured"
    assert news_sources[0]["enabled"] is True
    assert news_sources[0]["priority"] == 0
    assert news_sources[0]["config"]["market"] == "TW"
    assert news_sources[0]["test_symbols"] == ["2330", "0050"]
    assert news_sources[0]["config"]["items"] == []

    china_news = {row["provider"]: row for row in news_sources[1:]}
    assert china_news["eastmoney_news"]["test_symbols"] == ["601127", "600519"]
    assert china_news["eastmoney"]["test_symbols"] == ["601127", "600519"]
