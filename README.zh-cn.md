[English](/README.md) | [繁體中文](/README.zh-tw.md) | [简体中文](/README.zh-cn.md) | [日本語](/README.ja.md)

# InferSpec

**从你的代码 + Git 历史 + 文档反向推导出 OpenSpec 规范** —
专为没有规范的 legacy code 设计。

[![CI](https://github.com/anrylu/infer-spec/actions/workflows/ci.yml/badge.svg)](https://github.com/anrylu/infer-spec/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **From Code & Context to Clear Specs**

## 为什么需要 InferSpec？

你接手一个五万行的 Flask 服务。没有规范文档。只有一个三年没人动的 Jira 看板、一份没人更新的 Confluence wiki、还有一份 Git log。

**InferSpec 会把这些都读一遍**，产出结构化的 OpenSpec 规范 — 每个 capability 一份 `spec.md` — 并且每条 Requirement 都会回引到 `file:line` 或 ticket ID。AI 不确定的地方会标 `[GAP]`/`[TBD]`，让你之后可以互动式地补充。

## 工作原理

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — uvx Python 包：installer + CLI                    │
│  （永远不会调用 LLM API）                                       │
└─────────────────────────────────────────────────────────────┘
                       │ 把 skill 安装到
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2 — Skill 在 Claude Code / Codex / Gemini / Copilot  │
│  / OpenCode 内执行，使用 host 的 subscription AI               │
└─────────────────────────────────────────────────────────────┘
```

InferSpec 完全依赖你已经订阅的 AI 服务。不需要 API key、不需要配置云端 endpoint。

## 安装

```bash
uvx inferspec init --platform claude-code
```

这会把 `/inferspec-scan` 安装到当前目录的 `.claude/skills/`。完整支持平台列表可用 `inferspec platforms` 查看。

## 使用方式

在目标 repo 打开你的 AI agent，执行：

```
/inferspec-scan
```

这个 skill 会：
1. 跑 `graphify` 把文件分组成 capabilities
2. 对每个 capability，读取 code + `git log` + `docs/` + (如果有) 通过 MCP 的 Jira/Confluence + 通过 host 的 WebFetch 抓 URL
3. 用 OpenSpec 格式产出 `openspec/specs/<cap>/spec.md`

外部数据源（Jira、Confluence、URL）会自动处理 — InferSpec 检测你 host 环境里的 MCP server，不自己维护 client。

## 输出格式

跟 [OpenSpec](https://github.com/Fission-AI/OpenSpec) 同一套约定：

```markdown
## Purpose

订单入口的用户认证 — 因为 incident-1234 而取代了旧的 SSO bridge。
参考 AUTH-456。

## Requirements

### Requirement: Rate Limiting
系统 SHALL 在 60 秒内失败 5 次后拒绝登录请求。

**Source:** auth.py:18-21, [JIRA AUTH-456]

#### Scenario: 连续失败后锁定
- **GIVEN** 过去一分钟内已有 5 次失败
- **WHEN** 又一个 POST /auth/login 进来
- **THEN** server 返回 429
```

## 状态

**v0.1 alpha**。这版本提供 `/inferspec-scan`（bulk 模式）。互动式的 `/inferspec-cap` 跟 `/inferspec-refine` 会在 v0.2 推出。

## License

MIT
