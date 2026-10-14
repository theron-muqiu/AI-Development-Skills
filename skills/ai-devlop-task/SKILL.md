---
name: ai-devlop-task
description: 根据需求和设计生成 JSON 任务清单，明确场景覆盖、依赖、实现位置与完成标准。
---

# 实现任务拆分

读取本需求 `需求分析.json`、已有设计和项目规范，默认产出 `ai-devlop-task/任务清单.json`。完整读取同名 Schema 和示例。设计缺失时，仅在简单需求的实现位置、契约与数据影响均已明确时直接拆分，否则先解决设计缺口。已有清单定向修订，保留任务 ID、状态和完成依据。

按可交付业务结果拆分；内聚需求可以只有一个任务。不机械按 Controller、Service 或数据库分任务。每个任务写目标、场景引用、范围、位置、设计依据、前置任务、步骤和可验证完成标准。任务 ID 用 `T001` 起稳定编号，新增用更高未使用编号。依赖必须有效且无环；全部正常规则、异常、状态和验收均有承接。不自行缩小为 MVP，不编造负责人或工期。生成新任务状态为 pending；总览、场景覆盖和依赖视图由阅读器生成。

当前 Agent 顺序完成，不创建子代理，不实施代码，不擅改需求与设计。

## JSON 文档约定
先读取 `ai-devlop-spec/assets/文档格式.md` 的公共约定，再读取本技能 assets 下对应的 JSON Schema 与同名完整示例。示例只展示结构，不代表实际业务约定。JSON 使用 UTF-8、两空格缩进、英文属性名；说明文字可用 Markdown，图表保留 Mermaid。跨文档引用使用相对文件路径与稳定实体 ID；没有内容的集合用空数组。已有文档先读取再定向修订，保存前检查外部变更。

完成本轮文档修改后执行 `ai-devlop docs validate <需求目录>`，通过后执行 `ai-devlop docs render <需求目录>`，交付 JSON 与 `index.html`。源码环境可用 `uv run ai-devlop docs ...`；未长期安装 CLI 时，可经 `uvx --from "git+https://github.com/theron-muqiu/AI-Development-Skills.git@v0.4.0rc1" ai-devlop docs ...` 调用预发布版；正式版 v0.3.2 不支持此命令。校验或渲染失败时不得声称已同步完成，旧 HTML 仍是旧快照。
