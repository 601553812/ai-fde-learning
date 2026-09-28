# Day28 学习记录 — 逐任务审查批处理结果

## 学习开始

- 开始时间：2114
- 环境确认：使用仓库根目录 Python 3.11 `.venv`；本日练习为离线测试。

## 学习目标（无需提前作答）

- 从一份批处理报告里找到每条任务自己的 `raw`。
- 区分 `call_failed`、`invalid_structure`、`content_failed`、`content_passed` 与 `not_checked`。
- 说明写下的预期如何决定检查覆盖范围。

## 执行记录（学习后填写）

- 初始脚手架测试结果：学习者运行结果未记录；助手建立时为 127 passed / 7 项预期 TODO 失败。
- 完成后当天测试结果：助手复测 134 passed；全仓 992 passed。
- 主要错误及修正：起初在遍历 `expectations` 时追加结果，测试传入 B、A 因而输出顺序也是 B、A。学习者指出顺序问题后，助手按请求修正为先检查未知编号，再按 `report.tasks` 顺序审查。学习者写的失败 A / 无预期 B 边界测试已通过。

## 学习后复盘（实现后用自己的话回答）

1. 在 `code/batch_audit.py` 的 `audit_batch()` 中，报告按 A、B 排列：A 调用成功，`raw` 是 README 第 2 节的合法五字段 JSON；B 调用失败，`raw=None`。预期 A 的 `functions` 含 `PDF`，预期 B 的 `functions` 含 `CSV`。返回列表中 A、B 各自的 `status` 和 `issues` 是什么？按“A: status / issues；B: status / issues”回答。

   答案1（A 的 status / issues）：not_checked []

   答案2（B 的 status / issues）：call_failed []

2. 同一个函数收到一条调用成功的 C，`raw` 为合法五字段 JSON 且 `functions` 含 `CSV`，但 `expectations` 中没有 C。返回的 `status` 是什么？若之后给 C 写 `functions` 含 `CSV`、`risks` 为空的预期，状态将变为什么？此时能否断言未写入预期的其他需求也正确？按“无预期状态 / 加预期状态 / 理由”回答。

   答案1（没有预期时的 status）：

   答案2（加上预期后的 status）：

   答案3（其他需求能否断言正确及理由）：

3. 在 `tests/test_day28_extra.py` 的两任务例子中，只给失败的 A 写预期，成功的 B 没有预期。为什么不能只断言返回列表长度为 2？请写出还应检查的任务顺序、状态和问题列表，并说明一个可能通过长度断言却错误的实现。

   答案1（为什么只检查长度不够）：

   答案2（应检查的任务顺序）：

   答案3（A、B 各自的 status 和 issues）：

   答案4（长度仍为 2 的一种错误实现）：

## 错题本与验收反馈

- 2026-09-28 代码验收通过：当天 134 passed、全仓 992 passed；`pip check` 和提交前检查另见进度记录。核心 `audit_batch()` 的最终实现由助手按学习者明确请求完成，独立边界测试由学习者完成。不要把代码通过或下面的参考答案当成学习者独立掌握所有状态的证据。
- 第 1 题原答保留：A 写了 `not_checked / []`，但题目明确给 A 写了 PDF 预期。正确判断应为内容不符。用户今天表示无法集中，要求直接结束；不再要求补答或抄写。

### 助手参考答案（本日结束使用，非学习者独立作答）

1. A：`content_failed / ["missing:functions:PDF"]`；B：`call_failed / []`。A 有预期但原文仅含 CSV；B 没有可审查的成功调用原文。
2. 无预期：`not_checked`；加上所述预期：`content_passed`；不能断言未写入预期的其他需求正确。检查通过只覆盖指定的 CSV 片段和空 `risks`。
3. 还应检查返回顺序为 A、B；A 为 `call_failed / []`，B 为 `not_checked / []`。错误实现若返回 B、A 两项，长度仍是 2，长度断言不会发现顺序错误。学习者已在自己的边界测试中写出这些断言。

- 明日只用一个已有 A/B 例子复习：`expectations` 负责按编号提供检查条件，输出顺序由 `report.tasks` 决定；有预期但不符合是 `content_failed`，没有预期才是 `not_checked`。无需补交今天的空白答案或增加追赶练习。

## 学习反馈

- 实际用时（排除中断，自报）：未记录
- 难度与内容量：今日难以集中，学习者要求提前结束；未自评难度
- 仍需讲解的位置：明日仅复习预期有无与结果顺序

- 结束时间：2241
