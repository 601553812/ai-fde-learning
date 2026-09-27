# Day27 — 检查模型原文的结构与内容

状态：2026-09-27 已完成学习与验收。唯一主题是审查一次模型调用返回的 `raw`：先确认 JSON 结构，再用人工写下的明确要点核对内容。参考 90～120 分钟；Day26 自报 `2h-`、难度中。本日使用脱敏的本地文本，未调用 Gemini。

## 0. 按顺序开始

1. 在 [学习记录](./day27_notes.md) 填开始时间。以下命令均从仓库根目录运行，适用于 PowerShell 与 CMD/Cmder。
2. 先运行脚手架检查：

```text
.\.venv\Scripts\python.exe -m pytest Week4/day27/tests -q --tb=no
```

预期 **119 passed / 7 failed，退出码 1**。119 项中有从 Day26 复制且改为当天包路径的 118 项；另 1 项证明 `raw=None` 时无内容可检查。7 项失败均是本日 TODO。实现后不需要回退代码重现失败。
3. 先读第 1～2 节，再按 `code/ui.py` → `code/ui_client.py` → `code/app.py` → `code/batch.py` → `code/call_service.py` 看非测试调用链；接着读 `code/output_audit.py`，最后看 `tests/test_output_audit.py` 并做 TODO。`GeminiGateway.complete()` 的返回字符串就是 `CallResult.raw`。
4. 实现中可重跑当天测试。完成后按第 4 节验收，填写复盘、自报实际用时和难度；把结果交助手检查。

## 1. 用 Day26 已有例子复习（5 分钟）

一条 A 任务、`max_attempts=1`、`mode=live` 时，`summary.requests=1` 和 `summary.attempts=1` 可由输入及调用上限确定；模型若超时，`raw=None`。即使 HTTP 是 200，逐任务结果也可能失败。若 `raw` 是一个字符串，还需另外检查其结构与内容；`ok=True` 只说明调用返回了字符串。

## 2. 今天需要知道的最小知识（20 分钟）

```text
网关 complete(request) 返回原文字符串
  → call_once 放入 CallResult.raw
  → 批处理 API 返回 tasks[A].report.result.raw
  → 人工给 A 写预期：functions 应含 "CSV"、risks 应为空
  → audit_raw(raw, must_contain, must_be_empty)
  → 先检查五字段结构，再逐字段检查明确要点
```

`output_audit.py` 中已提供严格的 `ExtractedRequirements` 模型：五个字段都是 `list[str]`，额外字段禁止，字符串不能自动变成列表。`model_validate_json(raw, strict=True)` 类似 Java 中先把 JSON 反序列化为固定 DTO 再校验；类比的边界是 Pydantic 会按模型配置执行运行时校验，不能把 Python 类型标注本身看作校验代码。错误 JSON、少字段、字段类型不符或多字段都应视为 `invalid_structure`。这一步只回答“能否按约定解析”，不回答“CSV 需求是否提对”。

内容检查使用人工提前写下的可观察要点：`must_contain={"functions": ["CSV"]}` 表示 `functions` 的**某一项字符串**包含 `CSV` 子串；`must_be_empty=["risks"]` 表示 `risks` 必须是空列表。它适合验证明确片段，不是语义正确性的完整评估。例如某个无关句子碰巧含 `CSV` 也可能通过，需要人工再读原文。今天只比较给定的字段和子串，不做模糊匹配、LLM 评委、RAG、并发、费用统计或 Docker。Pydantic 用法可回看 [Day14 的模型输出校验](../../Week2/day14/README.md)；今天没有新依赖。

最小例子：`raw` 为 `{"functions":["一覧をCSVで出力する"],"acceptance_criteria":[],"risks":[],"questions":[],"unknown":[]}` 时，要求 `functions` 含 `CSV` 且 `risks` 为空，应得到 `content_passed`；把要求改为含 `PDF`，结构仍合法，但应得到 `content_failed` 与 `missing:functions:PDF`。模型调用失败的 `raw=None` 得到 `call_failed`，不假装做过结构或内容检查。

## 3. 三个 TODO（50～65 分钟）

### TODO 1：`code/output_audit.py` 的 `decode_raw`

目的：将模型原文校验为已提供的五字段模型。输入 `raw: str`；成功返回 `ExtractedRequirements`；JSON 不合法或结构不符时抛 `ValueError("invalid_structure")`，不要把可能含原文的底层异常文本放进错误消息。只改该函数。它不访问网络或文件，也没有退出码。

处理步骤：调用 `ExtractedRequirements.model_validate_json(raw, strict=True)`；捕获 `pydantic.ValidationError`，转换成上述固定错误并保留异常链。不要把本日页面的批处理响应模型 `BatchResponse` 当成模型原文的五字段模型。

### TODO 2：`code/output_audit.py` 的 `audit_content`

目的：对结构已合法的 `ExtractedRequirements` 检查人工预期。输入 `extracted`、`must_contain: dict[str, list[str]]`、`must_be_empty: list[str]`；返回按检查顺序排列的问题字符串列表，没问题返回 `[]`。本练习的预期字段名只使用五个模型字段，不要求处理未知字段；函数不抛业务异常、不写文件。

处理步骤：按 `must_contain` 的字段和每个期望片段的顺序，查看该字段的字符串列表；如果没有**任何一项**包含片段，追加 `missing:<字段>:<片段>`。随后按 `must_be_empty` 顺序检查；如果该字段的列表非空，追加 `unexpected:<字段>`。不要把整个列表转成一个字符串来比较，也不要因为结构合法就直接判内容通过。

### TODO 3：`tests/test_day27_extra.py` 的边界测试

目的：独立证明一个结构合法但 `risks` 不该有内容的结果会被拒绝。只改占位测试。用自制、五字段齐全的 JSON 文本，设置 `risks=["個人情報の確認が必要"]`，调用 `audit_raw(raw, {}, ["risks"])`；断言 `status == "content_failed"` 且 `issues == ["unexpected:risks"]`。测试函数无返回值；pytest 成功退出 0，失败退出 1。不需要 API key 或外部调用。

## 4. 实现后验收（15～20 分钟）

在仓库根运行：

```text
.\.venv\Scripts\python.exe -m pytest Week4/day27/tests -q
```

目标 **127 passed**。这包含复制的 Day26 行为测试与本日 9 个检查；其中多项字符串边界测试是在首次验收时针对本节既有“某一项包含片段”要求补上的。助手会在最终检查时看当前文件与差异，再按风险做必要的手动检查；复制包涉及导入路径，因此助手还会跑全仓回归，学习者无需重复跑所有旧日测试。

可选观察：若已有一次自己保存且脱敏的真实模型 `raw`，可在**本地、非仓库文件**中对照五字段和明确要点；不要把密钥、未脱敏客户材料或原始付费响应提交到公开仓库。本日完成标准以离线可重现测试、结构与内容两层判断、复盘为准；真实调用曾出现 timeout，不能把 `call_failed` 说成内容错误或内容通过。

## 5. 助手建立记录

- 从 Day26 复制代码、测试及脱敏样例到 `Week4/day27/`，统一改为当天包路径；历史 Day26 文件保持不变。新增审查模块和 8 个本日测试检查点，核心实现与独立边界测试留给学习者。
- 脚手架实测：**119 passed / 7 failed**；失败均指向本日 TODO。助手额外跑全仓回归为 **850 passed / 同 7 项失败**，历史测试仍通过；`pip check`、差异空白与常见密钥模式扫描通过。开始时间、实际用时与复盘由学习者填写，建立脚手架不代表本日已完成。
- 首次实现检查：原有当天 126 项测试通过；针对 TODO 2 已写明的“某一项字符串包含片段”，补测 `functions=["一覧をCSVで出力する", "検索も追加する"]` 后为 **126 passed / 1 failed**。这属于原测试覆盖不足，当前实现会误报 `missing:functions:CSV`；待修正后再做最终验收。
- 再次检查：学习者修正了多项字符串的判断，该边界测试已通过；当前 **123 passed / 4 failed**。四项是 `decode_raw()` 同一错误消息问题：`ValueError("invalid_structure", e)` 的字符串表示包含底层校验详情，不符合固定消息契约。详细反馈在当天笔记，尚未完成最终验收。
- 最终验收（2026-09-27）：学习者改用固定 `ValueError` 消息与 `from e` 异常链；本日 **127 passed**、助手全仓 **858 passed**、`pip check` 通过。手动确认坏 JSON 的公开错误消息为 `invalid_structure` 且原因为 `ValidationError`；多项字符串与非空 `risks` 的测试通过。两条既有依赖弃用警告不影响结果。学习者自报用时 2h、难度中；真实模型内容正确性未由本日离线测试证明。上方中途失败为历史记录。
