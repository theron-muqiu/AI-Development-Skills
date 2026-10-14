---
name: ai-devlop-implement
description: 按 JSON 任务依赖实施全部已授权任务，验证并同步真实状态与实现记录。
---

# 按任务实现

完整读取任务清单、需求、设计、项目规范及相关代码。按依赖顺序完成全部未完成任务，用户明确限定时遵守。保护工作区既有改动。当前 Agent 顺序完成，不创建子代理，不无目的扫描仓库。

逐任务实现正常、异常、权限、状态、事务和兼容行为。保持项目既有风格；新增或修改方法添加注释，关键逻辑添加简洁注释，Java 实体与 DTO 字段使用 `/** 注释 */`。Controller 不主动抽取公共方法；非 Controller 仅当本次产生超过 50 行重复代码且至少 3 处调用、用户未禁止时才允许抽取。Controller 每个接口入口记录 `[模块] 功能点 关键参数` 日志，关键业务节点与长链路按需记录状态、结果和阶段日志，避免敏感值。

执行任务完成标准和项目强制检查，失败时定位修复，不降低断言。实现与验证均满足后才把状态改为 completed；阻塞记 blocked，继续可独立执行的任务。返工时重开任务并写 reopenReason，保留历史验证事实。默认产出 `ai-devlop-implement/实现记录.json`，生成前完整读取同名 Schema 和示例；按实际时间记录任务结果、改动、命令、passed/failed/not_run 和剩余问题。最新记录须与清单当前状态一致，不能编造结果。部分完成如实报告。本地实现不自动授权提交、推送、合并、发布、部署或外部消息。

## JSON 文档约定
先读取 `ai-devlop-spec/assets/文档格式.md` 的公共约定，再读取本技能 assets 下对应的 JSON Schema 与同名完整示例。示例只展示结构，不代表实际业务约定。JSON 使用 UTF-8、两空格缩进、英文属性名；说明文字可用 Markdown，图表保留 Mermaid。跨文档引用使用相对文件路径与稳定实体 ID；没有内容的集合用空数组。已有文档先读取再定向修订，保存前检查外部变更。

完成本轮文档修改后执行 `ai-devlop docs validate <需求目录>`，通过后执行 `ai-devlop docs render <需求目录>`，交付 JSON 与 `index.html`。源码环境可用 `uv run ai-devlop docs ...`；未长期安装 CLI 时，可经 `uvx --from "git+https://github.com/theron-muqiu/AI-Development-Skills.git@v0.4.0rc1" ai-devlop docs ...` 调用预发布版；正式版 v0.3.2 不支持此命令。校验或渲染失败时不得声称已同步完成，旧 HTML 仍是旧快照。
