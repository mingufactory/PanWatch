# PanWatch Taiwan-first migration implementation plan

Date: 2026-06-28
Status: implementation plan only; no application code changed
Target integration branch: `dev`
Upstream preservation branch: `original-code`

## 1. Objective and boundaries

Migrate PanWatch from an A-share/China-first product to a Taiwan-first product while retaining CN/HK/US compatibility:

1. make Taiwan (`TW`) a first-class market and the default for new installations;
2. use Traditional Chinese (`zh-TW`) terminology and Taiwan conventions throughout the product;
3. add FinMind as the primary Taiwan market-data provider behind the existing provider orchestrators;
4. model Taiwan symbols, trading sessions, units, currency, benchmarks, holidays, and order constraints correctly;
5. migrate Taiwan news/event sources and AI prompts only after the market-data foundation is stable.

This is an additive migration. Existing `CN`, `HK`, and `US` rows, histories, settings, and providers must remain readable. Do not rename `CN` to `TW`, reinterpret existing six-digit symbols, or rewrite historical records in place.

Out of scope for the first release: brokerage order routing, tick-level streaming, complete TWSE/TPEx corporate-action accounting, and scraping Taiwan news sites without confirmed terms of use.

## 2. Findings from the current repository

### Reusable foundations

- `src/core/providers/` already defines quote, K-line, news, events, discovery, and capital-flow provider interfaces plus priority/failover orchestration.
- `DataSource` rows in `src/web/models.py` already support provider configuration, priority, enablement, test symbols, and UI-driven connection tests.
- Market-aware caches use `market + symbol` in most important paths, reducing collision risk when `TW` is added.
- `src/models/market.py` centralizes basic sessions, timezone, and symbol validation.

### China-first coupling that must be removed or isolated

- `MarketCode` only contains `CN/HK/US`; many APIs, frontend unions, fallback branches, and tests hard-code those three values. Several unknown-market paths silently coerce to `CN`.
- `src/collectors/akshare_collector.py` is actually a Tencent quote collector, owns A-share indices, and is directly imported by agents and APIs. This bypasses provider selection.
- `src/collectors/kline_collector.py` contains Tencent/EastMoney/Stooq routing, CN/HK-only fallback conditions, and CN benchmark mappings.
- `server.py` seeds China sample stocks and EastMoney/Tencent/Tushare-first sources. Seed updates are not currently migration-versioned, so existing installations and fresh installs can diverge.
- Currency and valuation are CNY-centric in `src/web/api/stocks.py`, `src/web/api/accounts.py`, `src/core/paper_trading_engine.py`, and `frontend/src/pages/Stocks.tsx` (`*_cny`, `HKD_CNY`, `USD_CNY`).
- Benchmark, factor, discovery, paper-trading, TradingAgents, prompt, and frontend market-label code frequently assumes `CN` is the default.
- `src/core/timezone.py` has compatibility functions named `beijing_*`; default timezone is `Asia/Shanghai` in both `src/config.py` and the helper.
- UI text and prompts are Simplified Chinese. This is broader than replacing “A股”: financial vocabulary, punctuation, date/time, currency, examples, and error messages require a controlled zh-TW glossary.
- The current weekday-only session check does not model exchange holidays. Taiwan logic must not claim the market is open solely because it is Monday–Friday.

## 3. Target design and decisions

### Market identity and symbols

- Add persisted code `TW`; never infer Taiwan from “numeric symbol” alone.
- Canonical user/database symbol is the exchange security code without a vendor suffix (examples: `2330`, `0050`, `006208`). Preserve leading zeroes as strings.
- Introduce a market-symbol module (for example `src/core/market_symbol.py`) with explicit `normalize`, `validate`, and vendor-format adapters. Keep `src/core/cn_symbol.py` as a compatibility wrapper until all CN callers move.
- Do not globally enforce four digits: Taiwan listed securities include ETFs and other valid lengths/patterns. Derive an allowlist/pattern from FinMind security master and use a conservative syntactic fallback when the master is unavailable.
- Store exchange/board metadata (`TWSE`, `TPEx`, emerging where supported) separately from `market=TW`; do not create a market enum per board.

### Taiwan market behavior

- Use `Asia/Taipei`, `TWD`, Taiwan date/number formatting, and Taiwan terminology (`台股`, `個股`, `成交量`, `漲跌幅`, `資料來源`, `自選清單`).
- Represent the regular session as 09:00–13:30. Auction, odd-lot, after-hours, suspension, and holiday states must be modeled as capabilities/data, not approximated as ordinary continuous trading.
- Add benchmark metadata for at least the Taiwan Weighted Index/TAIEX and make benchmark selection data-driven. Confirm the exact FinMind dataset/index identifier during implementation against a checked-in contract fixture or official documentation; do not bury it as an unexplained magic string.
- Treat volume units explicitly. Provider output should declare/normalize shares versus lots; do not reuse the current `StockData.volume` comment “手” for Taiwan.
- Add market metadata for currency, lot size, price-limit policy, timezone, and trading calendar. Strategy/backtest/paper-trading code consumes this metadata rather than branching on `CN`.

### FinMind integration

- Implement FinMind with existing `httpx`; no new Python dependency is expected unless implementation proves otherwise.
- Add one shared client/normalizer (`src/collectors/finmind_collector.py` or `src/core/providers/finmind_client.py`) and thin provider classes under `src/core/providers/quote/finmind.py` and `src/core/providers/kline/finmind.py`. Add discovery/events later, not in the first data slice.
- Expected initial datasets are security master, Taiwan daily prices, and trading dates. Dataset names, fields, adjustment semantics, authentication limits, and availability latency are implementation-time contract checks, not assumptions to encode untested.
- Be explicit that daily price data is not a real-time quote. If the available FinMind plan does not provide timely intraday quotes, expose `quote_kind=delayed|eod`, `as_of`, and staleness; disable “real-time” claims and price-alert behavior that requires live prices.
- Token lives only in environment/UI datasource config and is redacted in API responses/logs. Support anonymous access only if the provider contract allows it. Handle rate limiting, timeout, malformed rows, empty success, pagination, and stale-cache fallback.
- FinMind providers return current internal DTOs initially, then a follow-up refactor adds explicit provenance (`provider`, `dataset`, `as_of`, `adjustment`, `currency`, `volume_unit`) without breaking existing clients.

### Localization approach

- Establish `zh-TW` as the default locale and create a small shared frontend message catalog instead of continuing inline market labels. Backend messages and agent display metadata receive a corresponding glossary/module where practical.
- Localize by domain/page in reviewable branches. Do not run an unchecked character-conversion pass: terms such as 软件→軟體, 信息→資訊, 默认→預設, 账户→帳戶, and 盘前→盤前 require Taiwan usage review.
- Preserve stable API field names and database keys even when they contain legacy terms. User-visible labels change; wire contracts change only through separately versioned migrations.

## 4. Branch and integration strategy

`original-code` is immutable upstream reference. All implementation branches start from current `dev`, and all merges target `dev`; no feature branch targets `main` or `original-code`.

```text
original-code (reference only)
       \
        dev (integration, protected)
         ├─ feat/tw-market-domain
         ├─ feat/tw-finmind-provider
         ├─ feat/tw-portfolio-trading
         ├─ feat/zh-tw-localization
         ├─ feat/tw-news-prompts
         └─ docs/tw-release-readiness
```

Rules:

1. Rebase each feature branch on the latest `dev` before review; merge only after its phase gate passes.
2. Keep commits single-purpose using the repository convention (`feat:`, `fix:`, `test:`, `docs:`). Do not mix mass localization with provider logic.
3. Prefer short stacked branches where dependencies are unavoidable: market domain → FinMind → portfolio/trading → localization → news/prompts.
4. Use feature flags/settings (`default_market`, `locale`, provider enablement) until the Taiwan end-to-end gate passes. Flip fresh-install defaults only in the final readiness branch.
5. Tag a pre-migration `dev` point and document rollback. Rollback disables TW sources/defaults; it must not delete TW rows.

## 5. Phased implementation

### Phase 0 — contracts, fixtures, and compatibility baseline

Branch: `test/tw-contract-baseline`

- Define canonical TW examples and checked-in, sanitized FinMind response fixtures for successful, empty, malformed, rate-limited, and paginated responses. Fixtures must be captured/curated without tests calling external APIs.
- Add characterization tests for current CN/HK/US market parsing, provider fallbacks, portfolio valuation, API responses, and persisted enum strings.
- Write a zh-TW terminology glossary and inventory visible text. Decide which backend response messages are public UI contracts.
- Document FinMind account tier/token expectations and quote latency. This is a release blocker for enabling live alerts, not for daily K-lines.

Likely files: new `tests/fixtures/finmind/*.json`, `tests/test_market_compatibility.py`, `tests/test_finmind_contract.py`, and `docs/plans/` supporting notes if needed.

Gate: existing tests remain green; fixtures cover every field the normalizer consumes; no test uses network.

### Phase 1 — first-class Taiwan market domain

Branch: `feat/tw-market-domain`

- Add `MarketCode.TW` and Taiwan `MarketDef`; separate basic session checks from exchange calendar status.
- Add market metadata/capabilities and symbol normalization. Replace silent `else -> CN` fallbacks with validated errors or explicit configured defaults.
- Change application default timezone to `Asia/Taipei` for fresh installs while retaining `TZ/APP_TIMEZONE` overrides and legacy `beijing_*` aliases.
- Add Taiwan benchmark mapping and market-aware link behavior; unsupported external links must return none rather than a China URL.
- Extend Pydantic/API schemas and frontend TypeScript market types with `TW`, without yet making every feature available.

Primary files:

- `src/models/market.py`
- new `src/core/market_symbol.py`, optionally `src/core/market_metadata.py` and `src/core/trading_calendar.py`
- `src/core/cn_symbol.py`, `src/core/timezone.py`, `src/config.py`, `src/core/stock_link.py`
- `src/web/models.py`, `src/web/migrations.py`, `src/web/stock_list.py`
- `src/web/api/quotes.py`, `klines.py`, `market.py`, `stocks.py`, `discovery.py`, `insights.py`
- `frontend/src/pages/AnalysisDetail.tsx` and shared/new frontend market-type utilities

Tests:

- new `tests/test_tw_symbols.py`, `tests/test_tw_market.py`, `tests/test_market_validation.py`
- extend `tests/test_timezone.py`, `test_stock_link.py`, `test_index_klines.py`
- verify 4/5/6-character strings remain unambiguous when accompanied by market; unknown market returns 4xx instead of CN data.

Gate: `TW` round-trips through DB/API/UI types; CN/HK/US regressions pass; Taiwan session/timezone tests use fixed aware datetimes; no external calls.

### Phase 2 — FinMind security master, daily K-lines, and quote semantics

Branch: `feat/tw-finmind-provider`

- Build shared FinMind request, authentication, pagination, error classification, normalization, cache, and redaction logic.
- Implement K-line provider first, then quote provider using only a dataset whose latency semantics are known. Normalize sort order, duplicate dates, numeric nulls, OHLC, volume unit, currency, and adjustment status.
- Register providers in orchestrators and seed idempotent `finmind` datasource rows with Taiwan test symbols (`2330`, `0050`). FinMind is priority 0 for `TW` only and never receives CN/HK/US requests.
- Route all TW quote/K-line consumers through orchestrators. Do not add TW branches to Tencent/EastMoney collectors.
- Refactor the market-index API to use providers instead of directly calling Tencent.
- Add staleness/provenance to quote/API presentation so EOD data cannot trigger false real-time behavior.

Primary files:

- new `src/core/providers/finmind_client.py`
- new `src/core/providers/quote/finmind.py`, `src/core/providers/kline/finmind.py`
- `src/core/providers/orchestrator.py`, package `__init__.py` files
- `src/core/providers/base.py` if provenance DTOs are introduced
- `src/core/data_collector.py`, `src/collectors/kline_collector.py`, `src/collectors/akshare_collector.py`
- `server.py`, `src/web/api/datasources.py`, `src/web/api/quotes.py`, `klines.py`, `market.py`
- `frontend/src/pages/DataSources.tsx`, `Dashboard.tsx`, `Stocks.tsx`
- `requirements.txt` only if a justified dependency is unavoidable (expected: unchanged)

Tests:

- new `tests/test_finmind_client.py`, `test_finmind_quote_provider.py`, `test_finmind_kline_provider.py`
- extend `tests/test_quote_orchestrator.py`, `test_kline_orchestrator.py`, `test_kline_collector_cache.py`, `test_selfcheck.py`
- mock `httpx`/provider boundaries; assert no token in logs/errors; cover 401/403/429/5xx, timeout, empty payload, pagination, duplicate dates, stale data, cache key market isolation, and fallback.

Gate: fixture-backed `2330` and `0050` K-lines normalize deterministically; datasource tests work with mocked transport; CN/HK/US providers are unchanged; UI labels delayed/EOD data accurately.

### Phase 3 — Taiwan portfolio, alerts, strategy, and simulation logic

Branch: `feat/tw-portfolio-trading`

- Replace CNY-base assumptions with configurable base currency (fresh-install default `TWD`) and a generic FX map. Keep legacy response fields temporarily or add a versioned response; do not silently change `*_cny` meaning.
- Add TW allocation, TWD display, board lot/default quantity behavior, Taiwan fee/tax configuration, price-limit policy, benchmark, and market-calendar gating.
- Disable or clearly mark unsupported Taiwan capabilities (capital flow, announcements, discovery, intraday volume ratio) instead of falling back to EastMoney/A-share behavior.
- Make paper trading/backtests deterministic with configurable costs. Verify Taiwan sell-side transaction tax/fee assumptions with dated authoritative documentation before setting defaults.
- Update TradingAgents routing so TW symbols use PanWatch/FinMind data; do not let numeric TW symbols pass through A-share detection. Include market metadata, company name, currency, and data freshness in tool context.

Primary files:

- `src/core/portfolio_benchmark.py`, `portfolio_diagnostics.py`, `factor_weights.py`, `factor_eval.py`
- `src/core/paper_trading_engine.py`, `paper_trading_scheduler.py`, `price_alert_engine.py`
- `src/core/backtest/cost_model.py`, `engine.py`, `data_adapter.py`
- `src/core/strategy_engine.py`, `entry_candidates.py`, `prediction_outcome.py`, `context_builder.py`, `signals/signal_pack.py`
- `src/agents/intraday_monitor.py`, `daily_report.py`, `premarket_outlook.py`
- `src/agents/tradingagents/toolkit_adapter.py`, `financial_data.py`, `portfolio_context.py`, `history_comparison.py`, `backfill.py`, `agent.py`
- `src/web/api/accounts.py`, `stocks.py`, `paper_trading.py`, `price_alerts.py`, `factors.py`, `recommendations.py`, `suggestions.py`
- `frontend/src/pages/Stocks.tsx`, `PaperTrading.tsx`, `PriceAlerts.tsx`, `Opportunities.tsx`
- share-card and factor components under `frontend/src/components/`

Tests:

- new Taiwan cases for portfolio valuation, lot sizing, fee/tax, price limits, trading calendar, stale quote alert suppression, benchmark alignment, and TradingAgents routing.
- extend existing backtest, paper-trading, benchmark, factor, alert, context, and TradingAgents test modules identified under `tests/`.

Gate: a TWD portfolio containing `2330` and `0050` values correctly; TW simulation never uses CN fee/lot assumptions; stale EOD prices do not fire intraday alerts; existing CNY portfolios retain their prior values.

### Phase 4 — Traditional Chinese Taiwan localization and fresh-install defaults

Branch: `feat/zh-tw-localization`

- Add frontend locale/messages and replace inline visible strings page by page. Localize market labels, menus, forms, validation, empty states, source names, currency, dates, and share cards.
- Localize backend user-visible API errors, seeded agent names/descriptions, logs intended for users, PDF output, README, and sample watchlist. Preserve internal identifiers.
- Change fresh-install sample stocks to Taiwan examples and default filters to `TW`; use versioned/idempotent seeding so existing users are not overwritten.
- Set default locale `zh-TW`, timezone `Asia/Taipei`, base currency `TWD`, and Taiwan-first market ordering. Existing stored settings win.
- Add CJK font/render verification for PDF and screenshots; ensure Traditional Chinese glyphs are present in the container image.

Primary frontend files: `frontend/src/App.tsx`, every page under `frontend/src/pages/`, components with visible copy under `frontend/src/components/`, `frontend/src/lib/logger-map.ts`, `frontend/src/index.css`, plus new `frontend/src/i18n/zh-TW.ts` and locale helpers.

Primary backend/docs files: `server.py`, `config/watchlist.yaml`, `src/config.py`, `src/core/agent_catalog.py`, `src/core/pdf_export.py`, `src/core/selfcheck.py`, relevant `src/web/api/*.py`, `README.md`, `Dockerfile` if font coverage changes.

Tests/verification:

- frontend typecheck/build and component tests if a frontend test runner is added in a separate approved change;
- backend seed idempotency and legacy-setting tests;
- search gate for visible Simplified/A-share phrases with a reviewed allowlist for historical compatibility/code comments;
- manual desktop/mobile flows: login, dashboard, stocks, detail, agents, alerts, paper trading, settings, data sources, PDF/share cards.

Gate: new empty database opens Taiwan-first in zh-TW; existing database retains user stocks/settings; frontend builds; rendered PDF and major screens contain no missing glyphs or misleading A-share defaults.

### Phase 5 — Taiwan news, events, discovery, and AI prompts (later)

Branch: `feat/tw-news-prompts`

- Select Taiwan news, disclosure, and exchange-calendar sources only after reviewing availability, licensing/terms, attribution, rate limits, and stable identifiers. Prefer official TWSE/TPEx/MOPS sources for disclosures and calendars.
- Add TW-specific news/events/discovery providers through existing interfaces. Never send TW requests to EastMoney as an implicit fallback.
- Normalize article timezone, publisher, URL, symbols, dedupe key, language, and attribution. Defend against prompt injection in collected text.
- Create Taiwan prompt variants rather than editing all-market prompts in place. Include Taiwan benchmarks, TWD, market hours, daily price limits, disclosure terminology, data freshness, and explicit missing-data behavior.
- Update news ranking and agent symbol matching for four-digit/ETF symbols and Traditional Chinese aliases.

Primary files:

- new providers under `src/core/providers/news/`, `events/`, and `discovery/`
- `src/collectors/news_collector.py`, `events_collector.py`, `discovery_collector.py`
- `src/core/news_ranker.py`, `context_builder.py`, `data_collector.py`
- `src/agents/news_digest.py`, `daily_report.py`, `premarket_outlook.py`, `intraday_monitor.py`
- new `prompts/zh-TW/*.txt`; retain current prompts as compatibility variants
- `src/web/api/news.py`, `insights.py`, `discovery.py`, `context.py`, `chat.py`
- `frontend/src/pages/Stocks.tsx`, `Dashboard.tsx`, `DataSources.tsx`

Gate: all provider tests use fixtures; attribution is visible; TW news maps to the correct security without numeric ambiguity; prompt snapshots contain no A-share assumptions; hostile article fixture cannot override system instructions.

### Phase 6 — release hardening and default flip

Branch: `docs/tw-release-readiness`

- Run full backend suite, frontend build, offline integration suite, database upgrade/rollback rehearsal, container build, and smoke tests.
- Test three profiles: fresh Taiwan install; upgraded China-oriented install; mixed TW/CN/HK/US portfolio.
- Audit secrets/redaction, provider attribution, data latency labels, timezone boundaries, holidays, cache isolation, and backup/restore.
- Publish configuration/migration notes and capability matrix (real-time/delayed/EOD, quote/K-line/news/events per market).
- After gates pass, merge to `dev`, soak there, then promote through the repository's normal release process. `original-code` remains untouched.

## 6. Exact affected-file matrix

The following are the likely existing files to modify; additions are listed in the phases above.

| Area | Existing files |
|---|---|
| Market/config | `src/models/market.py`, `src/config.py`, `src/core/timezone.py`, `src/core/cn_symbol.py`, `src/core/stock_link.py`, `config/watchlist.yaml` |
| Provider registration/contracts | `src/core/providers/base.py`, `src/core/providers/orchestrator.py`, `src/core/providers/__init__.py`, quote/kline package `__init__.py` files, `src/core/data_collector.py` |
| Legacy collectors | `src/collectors/akshare_collector.py`, `kline_collector.py`, `capital_flow_collector.py`, `events_collector.py`, `news_collector.py`, `discovery_collector.py`, `screenshot_collector.py` |
| Seeds/persistence | `server.py`, `src/web/models.py`, `src/web/migrations.py`, `src/web/stock_list.py` |
| APIs | `src/web/api/quotes.py`, `klines.py`, `market.py`, `stocks.py`, `accounts.py`, `paper_trading.py`, `price_alerts.py`, `discovery.py`, `news.py`, `insights.py`, `context.py`, `factors.py`, `recommendations.py`, `suggestions.py`, `datasources.py` |
| Trading/analytics | `src/core/portfolio_benchmark.py`, `portfolio_diagnostics.py`, `factor_weights.py`, `factor_eval.py`, `paper_trading_engine.py`, `paper_trading_scheduler.py`, `price_alert_engine.py`, `strategy_engine.py`, `entry_candidates.py`, `prediction_outcome.py`, `context_builder.py`, `kline_context.py`, `signals/signal_pack.py`, `backtest/*.py` |
| Agents | `src/agents/daily_report.py`, `intraday_monitor.py`, `premarket_outlook.py`, `news_digest.py`, and `src/agents/tradingagents/{agent,backfill,financial_data,history_comparison,portfolio_context,toolkit_adapter}.py` |
| Prompts | `prompts/daily_report.txt`, `news_digest.txt`, `premarket_outlook.txt`, `intraday_monitor.txt`, `chart_analyst.txt` (prefer new locale variants) |
| Frontend | all `frontend/src/pages/*.tsx`; `frontend/src/App.tsx`; `frontend/src/components/{BenchmarkShareCard,DiagnosticsShareCard,DiscoveryPanel,FactorWeightsPanel,ShareCardDialog,ShareCardModal,SignalScoreShareCard}.tsx`; `frontend/src/lib/logger-map.ts`; new shared market/i18n modules |
| Docs/build | `README.md`, possibly `Dockerfile`, `build.sh` only if fonts/static locale packaging require it |
| Existing tests to extend | `tests/test_timezone.py`, `test_stock_link.py`, `test_index_klines.py`, `test_quote_orchestrator.py`, `test_kline_orchestrator.py`, `test_kline_collector_cache.py`, `test_backtest.py`, `test_portfolio_benchmark.py`, `test_portfolio_diagnostics.py`, `test_paper_trading_*.py`, `test_price_alert_volume_ratio.py`, `test_factor*.py`, `test_context_enrichments.py`, `test_tradingagents_*.py`, `test_selfcheck.py` |

## 7. Verification matrix

All automated tests must be offline. Block network in the test process and fail if an unmocked `httpx` call occurs.

| Layer | Required verification |
|---|---|
| Unit | TW symbol normalization, market metadata, fixed-time sessions, holiday/suspension state, FinMind normalization/error mapping, currency/lot/cost rules |
| Provider | fixture-backed auth, pagination, rate limit, timeout, malformed/empty data, sorting/deduplication, provenance, staleness, token redaction |
| Integration | datasource seed/priority, orchestrator market filtering/fallback/cache isolation, DB round-trip, API validation, upgraded settings |
| Regression | complete `pytest`; explicit CN/HK/US provider, valuation, TradingAgents, alert, and backtest cases |
| Frontend | `pnpm build` using already-installed dependencies in implementation environment; market unions, TW defaults, TWD formatting, zh-TW copy, delayed-data badge |
| Visual/manual | desktop/mobile critical paths, dark mode, long Traditional Chinese strings, PDF/share cards, empty/error/loading states |
| Release | fresh DB, upgraded DB copy, mixed-market DB; container smoke test; no secrets in DB export/logs; rollback disables features without data loss |

Implementation commands (when dependencies are already present):

```bash
pytest
pytest tests/test_finmind_client.py tests/test_finmind_quote_provider.py tests/test_finmind_kline_provider.py -q
cd frontend && pnpm build
git diff --check
rg -n 'A股|人民币|Asia/Shanghai|MarketCode\.CN|"CN"' src frontend/src prompts config server.py
```

The final `rg` is an audit, not an assertion that every match is wrong; compatibility code and CN market support remain valid.

## 8. Codex task breakdown

Each task is intended as one bounded Codex session/PR. Every task must begin by reading this plan and current `AGENTS.md`, must avoid network calls, and must report tests run plus residual risks.

1. **TW domain model:** add `TW`, metadata, symbol helpers, Taiwan timezone/session, strict market validation, and unit tests. No provider work.
2. **FinMind fixture contract:** add sanitized fixtures and client normalizer tests; define error/provenance types. No registration or UI changes.
3. **FinMind K-line provider:** implement and register TW-only K-lines, datasource seed, mocked tests, and index K-line support.
4. **FinMind quote semantics:** implement delayed/EOD or real-time quote path according to verified contract; propagate `as_of`/staleness; prevent stale alert use.
5. **API and seed migration:** extend schemas/filters, idempotent Taiwan datasource/sample seed, upgrade compatibility, and API tests.
6. **Portfolio/currency:** introduce base currency/TWD and generic FX contracts while preserving legacy CNY responses; add upgrade and valuation tests.
7. **Taiwan simulation rules:** add lot/cost/tax/price-limit/calendar policy with cited, dated assumptions and deterministic tests.
8. **TradingAgents adapter:** route TW explicitly through PanWatch, remove numeric A-share ambiguity, add Taiwan metadata/freshness, and extend isolation tests.
9. **Frontend market types/defaults:** centralize market metadata, add TW filters/forms/badges/TWD, and verify build. Keep copy changes limited.
10. **zh-TW shell and settings:** add message catalog/formatters and localize navigation, settings, datasource, auth, and common components.
11. **zh-TW portfolio/analysis pages:** localize Stocks, Dashboard, Opportunities, History, AnalysisDetail, Agents, alerts, and paper trading; perform visual QA.
12. **Taiwan news/events research implementation:** after source approval, add fixture-based providers, attribution/licensing notes, and dedupe/symbol tests.
13. **Taiwan prompts:** add locale/market prompt selection and zh-TW Taiwan prompt variants; snapshot-test A-share leakage and injection boundaries.
14. **Release hardening:** run compatibility matrix, fresh/upgraded/mixed DB rehearsal, docs, capability matrix, and rollback instructions; flip fresh-install defaults only here.

For tasks 2–4 and 12, Codex must not invent undocumented provider fields. If official contracts or approved fixtures are unavailable offline, stop at an interface/fixture TODO and report the blocker rather than implementing guessed parsing.

## 9. Risks and rollback

- **FinMind latency mistaken for real-time:** highest product risk. Mitigation: explicit quote capability and staleness; gate alerts/intraday agents.
- **Numeric symbol collision:** `2330`/`0050` can be misrouted by length heuristics. Mitigation: always carry market; reject ambiguous symbol-only entry points.
- **Unit/currency errors:** shares/lots and TWD/CNY errors can corrupt valuation. Mitigation: typed metadata, golden fixture calculations, preserve legacy contracts.
- **Calendar inaccuracies:** weekday checks produce false open-market state. Mitigation: trading-date provider plus cached calendar and fail-closed status.
- **Seed overwrite:** changing seeds can alter existing installations. Mitigation: versioned idempotent seeds; defaults apply only when absent.
- **Localization regression:** blind conversion can change identifiers or financial meaning. Mitigation: catalog/glossary, page-level review, no wire-key translation.
- **Provider outage/rate limit:** mitigation: bounded retry, TTL/stale cache, health metrics, clear degraded UI, no cross-market fallback.

Rollback procedure: disable FinMind/TW datasources and Taiwan-first feature flags/defaults on `dev`; restore the previous locale/default-market settings; retain all `TW` database rows for forward recovery. Code rollback must revert feature merges from `dev`, never reset or alter `original-code`, and never delete user data as part of rollback.

## 10. Definition of done

- Fresh install defaults to zh-TW, `Asia/Taipei`, `TWD`, and a Taiwan watchlist.
- `TW` is accepted and persisted everywhere without coercion to `CN`; CN/HK/US remain functional.
- FinMind data is normalized through provider interfaces, fully fixture-tested offline, correctly labeled for freshness, and secrets are redacted.
- Taiwan market hours, calendar, benchmark, symbol, volume, lot, currency, and simulation-cost behavior have deterministic tests.
- Unsupported Taiwan features degrade explicitly; no EastMoney/Tencent/A-share fallback is used for TW.
- Existing database upgrade preserves settings, histories, portfolios, and market meanings.
- Backend suite, frontend build, visual/PDF checks, and fresh/upgraded/mixed smoke profiles pass on `dev`.
- `original-code` remains untouched; implementation arrives through reviewed feature branches into `dev`; no migration work is committed directly to `main`.
