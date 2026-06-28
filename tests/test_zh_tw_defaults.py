"""Phase 4 fresh-install defaults and localization contract checks."""

from __future__ import annotations

import ast
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SAMPLES = [
    ("2330", "台積電"),
    ("0050", "元大台灣50"),
    ("2317", "鴻海"),
    ("2454", "聯發科"),
    ("2881", "富邦金"),
]


def _server_sample_literal() -> tuple[dict[str, str], ...]:
    tree = ast.parse((ROOT / "server.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if "FRESH_INSTALL_SAMPLE_STOCKS" in targets:
                return ast.literal_eval(node.value)
    raise AssertionError("FRESH_INSTALL_SAMPLE_STOCKS is missing")


def test_fresh_install_samples_are_taiwan_first() -> None:
    rows = _server_sample_literal()
    assert [(row["symbol"], row["name"]) for row in rows] == EXPECTED_SAMPLES
    assert {row["market"] for row in rows} == {"TW"}


def test_sample_seed_does_not_overwrite_existing_watchlist() -> None:
    source = (ROOT / "server.py").read_text(encoding="utf-8")
    function = next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == "seed_sample_stocks"
    )
    assert any(
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and any(isinstance(child, ast.Return) for child in node.body)
        for node in ast.walk(function)
    ), "seed must return before writes when stocks already exist"
    assert "seed.fresh_install_stocks.zh_tw.v1" in source
    assert 'value="skipped-existing"' in source


def test_yaml_watchlist_matches_fresh_install_samples() -> None:
    text = (ROOT / "config/watchlist.yaml").read_text(encoding="utf-8")
    assert re.findall(r"^\s+- code: (\w+)$", text, re.MULTILINE) == ["TW"]
    stocks = re.findall(
        r'^\s+- symbol: "([^"]+)"\n\s+name: "([^"]+)"$', text, re.MULTILINE
    )
    assert stocks == EXPECTED_SAMPLES


def test_prompts_use_taiwan_wording_without_china_first_assumptions() -> None:
    forbidden = ("主力淨流入", "主力净流入", "上证、深证", "美股表现对A股")
    for prompt in (ROOT / "prompts").glob("*.txt"):
        text = prompt.read_text(encoding="utf-8")
        assert "僅供參考" in text or prompt.name == "intraday_monitor.txt"
        assert not any(term in text for term in forbidden), prompt


def test_frontend_market_glossary_is_taiwan_first() -> None:
    glossary = (ROOT / "frontend/src/i18n/zh-TW.ts").read_text(encoding="utf-8")
    assert "MARKET_ORDER: MarketCode[] = ['TW', 'CN', 'HK', 'US']" in glossary
    assert "TW: '台股'" in glossary
    assert "CN: '中國 A 股'" in glossary
