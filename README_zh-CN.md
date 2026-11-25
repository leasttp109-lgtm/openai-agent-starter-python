# 出行决策 Agent (Python)

跑在 EdgeOne Makers 上的全栈 Python Agent：用户说出所在位置与想去的商场条件，Agent 通过**高德地图（合规地图数据源）**检索附近商场、计算距离，并给出推荐。基于 OpenAI Agents SDK（Python）的流式聊天，含自定义工具与 `context.store` 会话记忆。

**Framework：** OpenAI Agents SDK · **Category：** 出行决策 · **Language：** Python

[![Deploy to EdgeOne Makers](https://cdnstatic.tencentcs.com/edgeone/pages/deploy.svg)](https://console.cloud.tencent.com/edgeone/pages/new?template=openai-agents-starter-python)

<!-- ![preview](./assets/preview.png)  TODO: confirm -->

## 概述

把 OpenAI Agents SDK（Python）接到 EdgeOne Makers 上的出行决策应用。用户描述位置与店铺条件，Agent 按「解析位置 → 检索附近商场 → 计算距离」工具链给出推荐。

- **SSE 流式聊天** —— 逐 token 推 `text_delta`，命中工具时推 `tool_called`。
- **出行决策工具** —— `resolve_location` / `search_nearby_malls` / `compute_travel_distances`（见 `agents/_tools.py`）。
- **合规地图** —— 使用高德地图 WebService API，坐标 GCJ-02；Key 只从环境变量读取，绝不内嵌。
- **优雅降级** —— 距离接口不可用时自动用直线距离估算，保证推荐流程不中断。
- **会话粘性记忆** —— `context.store.openai_session(cid)` 直接喂给 `Runner.run_streamed()` 的 `session` 参数。
- **可信取消** —— 后端 `context.utils.abort_active_run()` 真正中断 LLM 调用。
- **后端拆两层** —— 有状态的长连接放 `agents/`，无状态的 `/history` 放 `cloud-functions/`。

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `AI_GATEWAY_API_KEY` | 是 | 模型网关 API Key。可填 Makers Models 的 API Key，也可以是任意 OpenAI 兼容服务商的 Key。 |
| `AI_GATEWAY_BASE_URL` | 是 | 网关 Base URL。Makers Models 请使用 `https://ai-gateway.edgeone.link/v1`。 |
| `AI_GATEWAY_MODEL` | 否 | 模型 ID。默认 `@makers/deepseek-v4-flash`（内置免费模型）。 |
| `AMAP_API_KEY` | 出行功能必填 | 高德地图 WebService API Key，用于位置解析/商场检索/距离计算。 |

模板遵循 OpenAI 兼容协议，可以指向 Makers Models，也可以指向任意 OpenAI 兼容的服务商。

### 如何获取 `AMAP_API_KEY`

1. 打开 [高德开放平台控制台](https://console.amap.com/)，用手机号登录并完成开发者实名认证（个人即可，有免费额度）。
2. 进入 **应用管理 → 我的应用 → 创建新应用**，填应用名称。
3. 在应用下 **添加 Key**，服务平台务必选择 **Web服务**。
4. 复制生成的 Key，写入本地 `.env` 的 `AMAP_API_KEY`，并在 EdgeOne Makers 控制台的 **项目设置 → 环境变量** 中同步添加后重新部署。
5. 未配置时的表现：Agent 会明确提示缺少 Key，不会伪造任何地点或店铺数据。

### 如何获取 `AI_GATEWAY_API_KEY`

1. 打开 [Makers 控制台](https://console.cloud.tencent.com/edgeone/makers)。
2. 登录并开通 Makers。
3. 进入 **Makers → Models → API Key**，新建一个 Key。
4. 把它粘到 `AI_GATEWAY_API_KEY`。

内置的 `@makers/deepseek-v4-flash` 免费但有用量限制，适合验证；生产建议自行绑定付费厂商（BYOK）。

## 本地开发

前置依赖：Node.js ≥ 18、Python ≥ 3.10，以及 EdgeOne CLI（`npm i -g edgeone`）。

```bash
npm install
pip install -r requirements.txt
cp .env.example .env       # 填入 AI_GATEWAY_API_KEY、AI_GATEWAY_BASE_URL、AMAP_API_KEY
edgeone makers dev
```

本地观测面板：`http://localhost:8080/agent-metrics`。

## 项目结构

```text
openAI-agent-starter-python/
├── agents/                          # 有状态的 EdgeOne Makers Agent Functions（Python）
│   ├── chat/index.py               # POST /chat —— SSE 流式聊天
│   ├── chat/stop.py                # POST /chat/stop —— 中断当前 agent
│   ├── _logger.py                  # 日志工具（私有）
│   ├── _tools.py                   # 出行决策四工具（私有）
│   └── _geo.py                     # 高德地图 WebService API 客户端（私有）
├── cloud-functions/                 # 无状态的 EdgeOne Makers Python cloud functions
│   ├── history/index.py            # POST /history —— 拉取对话消息
│   └── _logger.py                  # 日志工具
├── src/                             # React + Vite + TypeScript 前端
│   ├── App.tsx                     # 主应用 + SSE 流生命周期管理
│   ├── api.ts                      # /chat、/chat/stop、/history 接口封装
│   └── components/                 # ChatWindow、ChatInput、CodeViewer、ToolIndicators 等
├── package.json                     # 前端依赖
├── requirements.txt                 # Python 依赖
├── edgeone.json                     # framework=openai-agents-sdk
├── vite.config.ts
├── tsconfig.json
└── .gitignore
```

> 以 `_` 开头的文件是私有模块，不会暴露为公开路由。

## 资源

- [EdgeOne Makers Agents 文档](https://cloud.tencent.com/document/product/1552/132759)
- [EdgeOne Makers 快速开始](https://cloud.tencent.com/document/product/1552/132786)
- [Makers Models](https://cloud.tencent.com/document/product/1552/132748)

## License

MIT.
