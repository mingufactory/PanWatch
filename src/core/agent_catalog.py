"""Agent catalog and kind helpers.

Workflow agents are user-facing, schedulable pipelines.
Capability agents are internal/manual tools and should not be auto-scheduled.
"""

from __future__ import annotations

from dataclasses import dataclass


AGENT_KIND_WORKFLOW = "workflow"
AGENT_KIND_CAPABILITY = "capability"

WORKFLOW_AGENT_NAMES: tuple[str, ...] = (
    "premarket_outlook",
    "intraday_monitor",
    "daily_report",
)

CAPABILITY_AGENT_NAMES: tuple[str, ...] = (
    "news_digest",
    "chart_analyst",
)


def infer_agent_kind(agent_name: str | None) -> str:
    name = (agent_name or "").strip()
    if name in CAPABILITY_AGENT_NAMES:
        return AGENT_KIND_CAPABILITY
    return AGENT_KIND_WORKFLOW


def is_workflow_agent(agent_name: str | None) -> bool:
    return infer_agent_kind(agent_name) == AGENT_KIND_WORKFLOW


def is_capability_agent(agent_name: str | None) -> bool:
    return infer_agent_kind(agent_name) == AGENT_KIND_CAPABILITY


@dataclass(frozen=True)
class AgentSeedSpec:
    name: str
    display_name: str
    description: str
    enabled: bool
    schedule: str
    execution_mode: str
    kind: str
    visible: bool
    lifecycle_status: str = "active"
    replaced_by: str = ""
    display_order: int = 0
    config: dict | None = None


AGENT_SEED_SPECS: tuple[AgentSeedSpec, ...] = (
    AgentSeedSpec(
        name="premarket_outlook",
        display_name="盤前分析",
        description="開盤前綜合前一交易日分析與隔夜資訊，整理今日展望",
        enabled=False,
        schedule="0 9 * * 1-5",
        execution_mode="batch",
        kind=AGENT_KIND_WORKFLOW,
        visible=True,
        display_order=10,
    ),
    AgentSeedSpec(
        name="intraday_monitor",
        display_name="盤中監測",
        description="交易時段監控行情，由 AI 判斷值得留意的訊號",
        enabled=False,
        schedule="*/5 9-15 * * 1-5",
        execution_mode="single",
        kind=AGENT_KIND_WORKFLOW,
        visible=True,
        display_order=20,
        config={
            "event_only": True,
            "price_alert_threshold": 3.0,
            "volume_alert_ratio": 2.0,
            "stop_loss_warning": -5.0,
            "take_profit_warning": 10.0,
            "throttle_minutes": 30,
        },
    ),
    AgentSeedSpec(
        name="daily_report",
        display_name="收盤複盤",
        description="每日收盤後產生複盤報告，包含市場回顧、個股分析與次日重點",
        enabled=True,
        schedule="30 15 * * 1-5",
        execution_mode="batch",
        kind=AGENT_KIND_WORKFLOW,
        visible=True,
        display_order=30,
    ),
    AgentSeedSpec(
        name="news_digest",
        display_name="新聞快訊（能力）",
        description="內部能力：提供新聞擷取、去重與主題彙整，不獨立排程",
        enabled=False,
        schedule="",
        execution_mode="batch",
        kind=AGENT_KIND_CAPABILITY,
        visible=False,
        lifecycle_status="deprecated",
        replaced_by="premarket_outlook,daily_report,intraday_monitor",
        display_order=110,
        config={
            "since_hours": 12,
            "fallback_since_hours": 24,
        },
    ),
    AgentSeedSpec(
        name="chart_analyst",
        display_name="技術分析（能力）",
        description="內部能力：在詳細頁面依需求觸發圖表技術分析，不獨立排程",
        enabled=False,
        schedule="",
        execution_mode="single",
        kind=AGENT_KIND_CAPABILITY,
        visible=False,
        lifecycle_status="deprecated",
        replaced_by="intraday_monitor,daily_report,premarket_outlook",
        display_order=120,
    ),
    AgentSeedSpec(
        name="tradingagents",
        display_name="TradingAgents 深度分析",
        description="多 Agent 投資決策框架（基本面／情緒／新聞／技術、正反方辯論、風險控管與 PM）。"
        "單次約 3–5 分鐘、約 US$0.05（deepseek-chat）；需手動觸發，預設關閉。",
        enabled=False,
        schedule="",
        execution_mode="single",
        kind=AGENT_KIND_WORKFLOW,
        visible=True,
        display_order=40,
        config={
            "analyst_types": ["market", "social", "news", "fundamentals"],
            "debate_rounds": 1,
            "monthly_budget_usd": 10.0,
            "over_budget_action": "reject",
            "cache_ttl_hours": 12,
            "output_language": "Chinese",
            "deep_model": "",       # 留空走默认 AI Service 的 model;可填如 "claude-sonnet-4"
            "quick_model": "",      # 留空 = deep_model;可填便宜模型如 "deepseek-chat"
            "timeout_minutes": 15,
            "emit_paper_trading_signal": False,  # 是否把 BUY 决策写入 StrategySignalRun
                                                  # 驱动模拟盘自动开仓 (默认关,需用户主动启用)
        },
    ),
)
