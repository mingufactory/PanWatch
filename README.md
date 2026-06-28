# PanWatch 台股盯盤助手

**自架 AI 盯盤助手 · 整合 [TradingAgents](https://github.com/TauricResearch/TradingAgents) 多 Agent 投資決策** — 以台股為預設，並保留中國 A 股、港股與美股相容性

[![GitHub stars](https://img.shields.io/github/stars/TNT-Likely/PanWatch?style=flat&logo=github&color=yellow)](https://github.com/TNT-Likely/PanWatch/stargazers)
[![Docker Pulls](https://img.shields.io/docker/pulls/sunxiao0721/panwatch?logo=docker&label=docker%20pulls&color=2496ED)](https://hub.docker.com/r/sunxiao0721/panwatch)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Last commit](https://img.shields.io/github/last-commit/TNT-Likely/PanWatch)](https://github.com/TNT-Likely/PanWatch/commits/main)
[![PWA](https://img.shields.io/badge/PWA-installable-5A0FC8?logo=pwa&logoColor=white)](https://github.com/TNT-Likely/PanWatch)

![盯盘侠 PanWatch · TradingAgents 深度分析演示](docs/screenshots/tradingagents-demo.gif)

> 🧠 **持仓页点一下 → TradingAgents 9-Agent 投研团队接力分析 → 看多看空辩论 → 风控审查 → PM 决策书,3-5 分钟一条完整推理链,结论直推到你的 IM。**

## 📸 功能一览

| 持仓 · 多账户汇总 | 机会页 · AI 评分选股 |
|:---:|:---:|
| ![持仓管理](./docs/screenshots/portfolio.png) | ![机会页 AI 评分](./docs/screenshots/opportunities.png) |
| **模拟盘 · 净值曲线 + 绩效** | **个股深度详情** |
| ![模拟盘](./docs/screenshots/papertrading.png) | ![个股详情](./docs/screenshots/stock-detail.png) |
| **技术指标共振 · 一眼 MACD/RSI/KDJ** | **价格提醒 · 条件组合触发** |
| ![技术指标](./docs/screenshots/technicals.png) | ![价格提醒](./docs/screenshots/alerts.png) |

<details>
<summary>移动端截图</summary>

<img src="./docs/screenshots/mobile.png" width="300" /> <img src="./docs/screenshots/mobile-detail.png" width="300" />

> 📱 支持 PWA，移动端可「添加到主屏幕」当原生 App 用。

</details>

> 💡 如果盯盘侠对你有帮助，点右上角 ⭐ **Star** 支持一下 —— 这是对开源项目最好的鼓励，也能让更多人发现它。

## 🧠 深度分析：TradingAgents 多 Agent 决策

接入 [TradingAgents](https://github.com/TauricResearch/TradingAgents)（76k+ star）多 Agent 投资决策框架，在持仓页点 🧠 图标即可触发：

- **4 类分析师**（技术 / 情绪 / 新闻 / 基本面） → **看多看空辩论** → **风控审查** → **PM 整合决策**
- 3-5 分钟输出完整推理链，结论同步推送到 Telegram / 微信 / 钉钉
- 默认 deepseek-chat，单次 ~$0.05，月度预算可控

## 為什麼選擇 PanWatch？

- **資料自主** — 自架部署，持倉資料由你管理
- **AI 原生** — 讓 AI 綜合持倉、交易風格與目標，而非只堆疊指標
- **快速部署** — 使用 Docker 約 5 分鐘完成基本設定

## 核心功能

<details>
<summary><b>智能 Agent 系统</b></summary>

| Agent | 触发时机 | 功能 |
|-------|---------|------|
| **盘前分析** | 每日开盘前 | 综合隔夜美股、新闻消息、技术形态，给出今日操作策略 |
| **盘中监测** | 交易时段实时 | 监控异动信号，RSI/KDJ/MACD 共振时推送提醒 |
| **盘后日报** | 每日收盘后 | 复盘当日走势，分析资金流向，规划次日操作 |
| **新闻速递** | 定时采集 | 抓取财经新闻，AI 筛选与持仓相关的重要信息 |

</details>

<details>
<summary><b>专业技术分析</b></summary>

- **趋势指标**：MA 多空排列、MACD 金叉死叉、布林带突破
- **动量指标**：RSI 超买超卖、KDJ 钝化与背离
- **量价分析**：量比异动、缩量回调、放量突破
- **形态识别**：锤子线、吞没形态、十字星等 K 线形态
- **支撑压力**：自动计算多级支撑位和压力位

</details>

<details>
<summary><b>多市場與多帳戶</b></summary>

- **涵蓋市場**：台股優先，並相容中國 A 股、港股與美股；資料即時性依啟用的 provider 而定
- **帳戶管理**：支援多個券商帳戶獨立管理及資產彙總
- **交易風格**：可依短線、波段與長線分別設定

</details>

<details>
<summary><b>全渠道通知</b></summary>

Telegram / 企业微信 / 钉钉 / 飞书 / Bark / 自定义 Webhook

</details>

<details>
<summary><b>价格提醒</b></summary>

- 支持价格、涨跌幅、成交额、量比等条件组合（AND / OR）
- 支持交易时段/全天生效、冷却时间、日触发上限、重复触发模式
- 到期时间使用弹窗内日期面板 + `HH:mm` 输入，留空表示永不过期
- 可按规则选择通知渠道，不选则走系统默认渠道

</details>

## 快速開始

```bash
docker run -d \
  --name panwatch \
  -p 8000:8000 \
  -v panwatch_data:/app/data \
  sunxiao0721/panwatch:latest
```

開啟 `http://localhost:8000`，首次使用時設定帳號密碼。全新安裝會以 `Asia/Taipei` 與台股為預設，並加入台積電（2330）、元大台灣50（0050）、鴻海（2317）、聯發科（2454）及富邦金（2881）作為自選清單範例；既有資料庫不會被覆寫。

說明：映像檔已包含 Playwright 所需的系統相依套件；Chromium 會在容器首次啟動時下載至掛載磁碟區（預設 `/app/data/playwright`），可能需要數分鐘及可用的網路連線。

若不需要圖表截圖，可在啟動容器時設定 `PLAYWRIGHT_SKIP_BROWSER_INSTALL=1`，略過 Chromium 安裝。

<details>
<summary>Docker Compose</summary>

```yaml
version: '3.8'
services:
  panwatch:
    image: sunxiao0721/panwatch:latest
    container_name: panwatch
    ports:
      - "8000:8000"
    volumes:
      - panwatch_data:/app/data
    restart: unless-stopped

volumes:
  panwatch_data:
```

```bash
docker-compose up -d
```

</details>

<details>
<summary>環境變數</summary>

| 變數名稱 | 說明 | 預設值 |
|--------|------|--------|
| `AUTH_USERNAME` | 预设登录用户名 | 首次访问时设置 |
| `AUTH_PASSWORD` | 预设登录密码 | 首次访问时设置 |
| `JWT_SECRET` | JWT 签名密钥 | 自动生成 |
| `DATA_DIR` | 数据存储目录 | `./data` |
| `TZ` | 應用程式時區（影響 Agent 排程與時間顯示） | `Asia/Taipei` |
| `PLAYWRIGHT_SKIP_BROWSER_INSTALL` | 跳过首次 Chromium 安装（不需要截图时可用） | 未设置 |
| `LOG_LEVEL` | 控制台日志级别。默认 `INFO`（只输出业务事件 + 错误）；排查问题时设 `DEBUG` 可看到调度心跳、采集过程等底层日志。UI 日志板始终保留完整记录，不受影响 | `INFO` |
| `HTTP_PROXY` / `HTTPS_PROXY` / `http_proxy` | 出站 HTTP 代理。三种配置方式任选其一: ① 启动前 `export HTTP_PROXY=...`；② `.env` 里写 `http_proxy=http://host:port`；③ UI「设置 → 全局 HTTP 代理」。三者优先级:外部环境变量 > UI > `.env`。生效后所有 httpx 客户端走代理。`NO_PROXY` 默认包含 `localhost,127.0.0.1` | 未设置 |

</details>

<details>
<summary>首次設定</summary>

1. 開啟 Web 介面並設定登入帳號。
2. 前往「設定 → AI 服務商」，設定 OpenAI 相容 API。
3. 前往「設定 → 通知管道」，加入 Telegram 或其他推播管道。
4. 前往「持倉 → 新增股票」，調整自選清單並啟用需要的 Agent。

</details>

<details>
<summary>本地开发</summary>

**环境要求**：Python 3.10+ / Node.js 18+ / pnpm

```bash
# 一键开发（推荐）
make dev-api          # 启动后端（自动 venv+依赖，监听 :8000）
make dev-web          # 启动前端（自动 pnpm install，监听 :5183）

# 或手动
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python server.py                              # 后端 :8000

cd frontend && pnpm install && pnpm dev       # 前端 :5183
```

前端 dev server 跑在 `http://localhost:5183`，并把 `/api` 代理到 `127.0.0.1:8000`。
前端用 `:5183` 而非默认 `:5173`，是为了和 BeeCount-Cloud 等本地常驻前端错开。

</details>

<details>
<summary><b>技术栈</b></summary>

**后端**：FastAPI / SQLAlchemy / APScheduler / OpenAI SDK

**前端**：React 18 / TypeScript / Tailwind CSS / shadcn/ui

</details>

<details>
<summary><b>发布（Docker 镜像）</b></summary>

本项目内置 GitHub Actions 发布流程：

- 打 tag（例如 `0.2.3`）会自动构建并推送 Docker 镜像
  - `sunxiao0721/panwatch:0.2.3`
  - `sunxiao0721/panwatch:latest`
- 也支持在 GitHub Actions 里手动触发（workflow_dispatch）指定版本号

需要在仓库 Secrets 中配置：

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

</details>

## 捐赠支持

如果你觉得 PanWatch 有帮助，欢迎请作者喝杯咖啡：

| 微信赞赏 | 支付宝 |
|:---:|:---:|
| <img src="./docs/donate/wechat.png" width="240" /> | <img src="./docs/donate/alipay.png" width="240" /> |

## 贡献

欢迎提交 Issue 和 PR！自定义 Agent 和数据源开发请参考 [贡献指南](CONTRIBUTING.md)。
社区交流（Telegram）：[t.me/panwatch](https://t.me/panwatch)

## License

[MIT](LICENSE)
