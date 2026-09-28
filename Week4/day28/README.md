# Day28 — 逐任务审查批处理结果

状态：2026-09-28 已结束；代码与离线测试验收通过，复盘使用助手参考答案，独立概念掌握未由本日复盘证明。本日唯一主题是把 Day27 的单条 `audit_raw()` 用在一份批处理报告中。只用自制的离线结果，未调用 Gemini。

## 0. 按顺序开始

1. 在 [学习记录](./day28_notes.md) 填开始时间。以下命令从仓库根目录运行，适用于 PowerShell 与 CMD/Cmder；使用根目录 Python 3.11 `.venv`。
2. **先运行初始脚手架检查**：

```text
.\.venv\Scripts\python.exe -m pytest Week4/day28/tests -q --tb=no
```

预期 **127 passed / 7 failed，退出码 1**。127 项保留从 Day27 复制并改为当天包路径的行为；6 项失败指向 `audit_batch()`，1 项失败是留给你写的边界测试。它们是尚未实现的 TODO，不是已完成代码的故障。实现后无需回退代码重现初始失败。
3. 读第 1～2 节，再按 `code/app.py` → `code/response_models.py` → `code/output_audit.py` → `code/batch_audit.py` 看**非测试代码**，弄清一份 HTTP 响应如何变为 `BatchResponse`、单条原文如何变为 `AuditResult`。最后看 `tests/test_batch_audit.py`，开始 TODO。
4. 实现时重跑当天测试；完成后按第 4 节验收，填写复盘、实际用时和难度，再交助手检查。

## 1. 用已有例子复习（5 分钟）

Day27 的原文 `functions=["一覧をCSVで出力する"]`，只写 `functions` 含 `CSV` 与 `risks` 为空时，`content_passed` 只证明这两个明确条件通过；其余需求没有被这次检查证明。今天两项任务 A、B 即使得到相同原文，也可以因各自预期不同而得到不同结果。先把这句话与 [Day27 的 `audit_raw()`](../day27/code/output_audit.py) 对上，无需补交 Day27 复盘。

## 2. 最小知识与调用链（20 分钟）

```text
POST /analyze-batch → tasks[A/B].report.result.raw
  → response_models.BatchResponse 校验整份响应
  → audit_batch(已校验报告, 按 task_id 写下的预期)
  → 对每条有预期的模型原文调用 Day27 的 audit_raw()
  → 得到按原任务顺序排列的 TaskAudit 列表
```

本日直接使用 `BatchResponse` 作为函数输入，不修改 API 或页面。现有 `ui_client.validate_report()` 内部也使用这个模型校验 API 报告，但它向页面返回的是字典；本题测试直接构造模型。`BatchResponse.tasks` 中每条的 `task_id` 与 `report.result.ok/raw` 是已校验后的属性；`expectations["A"]` 是给 A **事先写下**的检查条件。这里的字典按任务编号查找，类似 Java `Map<String, AuditExpectation>`；Python 字典的具体语法不同，但本题只需 `in` 与 `[...]`。`TaskAudit` 是一次审查的记录，不会改写原来的模型调用报告。

最小例子：A、B 的 `raw` 都是合法五字段 JSON，`functions` 都含 `CSV`。给 A 的预期是 `CSV`、给 B 的预期是 `PDF`，则 A 为 `content_passed`，B 为 `content_failed` 且问题是 `missing:functions:PDF`。如果 B **没有写预期**，B 是 `not_checked`，不能把它显示为通过。若调用本身失败，则是 `call_failed`；结构不合法是 `invalid_structure`。这些状态各自回答不同问题。

今天无需学习新库；Day27 的 [Pydantic 校验说明](../day27/README.md) 和本日现有代码足够。暂不学 RAG、模糊匹配、LLM 评委、并发、费用统计或 Docker。Week4 路线要求的 Docker 可运行闸门仍需有可执行环境再验证；当前机器没有 `docker` 命令，本日不能凭测试宣称已完成该闸门。

## 3. 两个 TODO（50～65 分钟）

### TODO 1：`code/batch_audit.py` 的 `audit_batch`

目的：对批处理的每条结果给出**独立**的审查状态。只修改这个函数。输入为已校验的 `BatchResponse report` 和 `dict[str, AuditExpectation] expectations`；输出为 `list[TaskAudit]`，顺序与 `report.tasks` 一致。它不调用网络或写文件，没有 CLI 退出码。

按以下顺序处理：

1. 先找出 `expectations` 中不属于 `report.tasks` 的任务编号。遇到第一个未知编号，就抛 `ValueError("unknown_expectation:<编号>")`，不得开始审查。空报告与空预期返回空列表。
2. 逐条遍历 `report.tasks`。若 `row.report.result.ok` 为 `False`，记录 `TaskAudit(task_id, "call_failed", [])`，不调用内容检查；即使该任务没有预期，也要如实记录调用失败。
3. 调用成功但该 `task_id` 没有写预期时，记录 `TaskAudit(task_id, "not_checked", [])`。不能把“无条件可检查”当成内容通过。
4. 调用成功且有预期时，将该任务的 `raw`、`must_contain`、`must_be_empty` 交给已有的 `audit_raw()`，把返回的 `status` 与 `issues` 写进 `TaskAudit`。`raw=None` 时沿用 `audit_raw()` 的 `call_failed` 规则。不要自己重写 Day27 的结构或内容算法。
5. 返回列表，不修改 `report` 或 `expectations`。保留不同任务各自的问题，不合并成一个总状态。

### TODO 2：`tests/test_day28_extra.py` 的独立边界测试

目的：证明**失败调用**与**成功但没有写预期**不会被混成同一状态。只改占位测试；可使用该文件已导入的 `report()`、`raw()`、`expected()`、`audit_batch()`。构造按 A、B 排列的报告：A 的原文为 `None`（调用失败），B 的原文为 `raw()`（调用成功）。只给 A 写 `expected()`，B 不写预期。调用后断言返回列表的两个 `task_id` 顺序、两个 `status` 分别为 `call_failed` / `not_checked`，且两条 `issues` 都是 `[]`。测试函数不返回业务值；pytest 通过退出 0，断言失败退出 1。不要发起 API 请求。

## 4. 实现后验收与复盘（15～20 分钟）

从仓库根运行：

```text
.\.venv\Scripts\python.exe -m pytest Week4/day28/tests -q
```

目标 **134 passed**。检查 A/B 预期不同、调用失败、坏结构、无预期、空批次与未知编号都符合第 3 节契约；助手会看当前文件和差异，并因复制包路径运行全仓回归。学习者无需重复运行已完成日的全部测试。完成后在笔记中用自己的话回答具体复盘题，自报实际用时与难度。本日不能凭离线测试证明真实 Gemini 的内容语义正确。

## 5. 助手建立记录

- 从 Day27 复制代码、测试与脱敏样例到 `Week4/day28/`，将包导入改为当天路径；Day27 历史文件保持不变。新增逐任务审查函数及 6 个契约测试，核心实现与独立边界测试留给学习者。
- 初始脚手架：当天 **127 passed / 7 项预期 TODO 失败**；助手全仓 **985 passed / 同 7 项失败**，历史 858 项与复制的 127 项均通过。已有两条依赖弃用警告。Docker 命令当前不可用，未把 Docker 闸门标为通过。
- 收尾（2026-09-28）：学习者完成独立边界测试；核心函数由助手按明确请求修正，先检查未知编号，再按报告顺序逐条审查。当天 **134 passed**、全仓 **992 passed**。学习者要求直接结束；原有答案与空白保留，参考答案和唯一明日复习点见 [学习记录](./day28_notes.md)。实际用时未自报，不以时钟差代替。上方 TODO 与初始失败为历史练习说明。
