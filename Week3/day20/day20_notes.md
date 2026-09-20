# Day 20 学习记录 — 有限次数重试

## 学习开始

- 开始时间：1412
- 环境确认：原项目根目录、根 .venv Python 3.11；按 README 第 0 节先检查脚手架。

## 本日学习目标（无需提前作答）

- 区分一次调用结果与外层重试决定；解释何时继续、何时返回。
- 保留最新一次失败，控制实际请求次数和等待顺序。
- Day18 真实对比继续留空，不补交；本日模拟不代表真实模型效果。

## 执行记录（做完再填）

- 初始测试：学习者终端记录未提供；助手建立脚手架时为 23 passed / 18 项 TODO 预期失败。
- 实现后本日测试 / 全仓测试：助手本轮实测 41 passed / 234 passed，退出 0；不代表学习者终端执行记录。

| 场景 | result.ok | result.error | result.status_code | attempts | 退出码 |
|---|---|---|---|---|---|
| recover | True | None | None | 2 | 0 |
| exhausted --max-attempts 2 | False | service_unavailable | 503 | 2 | 1 |
| auth_after_503 | False | auth_error | 403 | 2 | 1 |

上表由助手根据本轮验收补记；均为本地模拟，不代表学习者终端日志或真实模型结果。

## 学习后复盘

用字段值或 1～2 句回答；条件全部在题目里，不要求先调用真实模型。

1. 在 `retry_service.py` 的 `call_with_retry` 中，`max_attempts=2`，gateway 每次都抛 503。预期 `report.result.error`、`report.attempts`、`sleep.calls` 分别是什么？若上限改为 1，调用次数和等待记录分别是什么？这里检查“总调用上限”与“额外重试次数”的区别。

   回答：report.result.error = "service_unavailable"  report.attempts=2 sleep.calls=[0.2]
            若上限改为 1，调用次数和等待记录分别是1,[]

2. 在 `test_day20_extra.py`，结果按 503 → 403 → 字符串排列，上限是 3。正确实现应返回哪次失败？如果错误实现忽略第二次 403，仍调用第三次并返回成功，你写的哪一项断言会失败？任选一项，写出它的期望值与错误实现的实际值；测试失败本身不等于直接诊断出根因。

   回答：403      assert gateway.calls == [request, request]会失效 实际值是 [request, request, request]

3. 在 `test_retry.py` 的 `test_success_stops_without_sleep_even_for_invalid_json`，第一次 complete 正常返回 `"not-json"`。预期 attempts 和 sleep.calls 是什么？为什么这里不重试？这份成功结果是否证明 JSON 合法或内容准确？这里检查调用、结构、内容三层的区别。

   回答：attempts=1 sleep.calls=[] 因为正常返回了 不能证明 因为校验的是有没有发生error 没有校验返回无效字符串

## 错题本与验收反馈

当前结论：Day20 已完成。以下检查与订正按发生顺序保留；其中“待巩固”等属于历史过程，最新结论见末尾最终复核。

### 助手检查（2026-09-20；保留上方原答）

- 代码与运行验收通过：Day20 41 passed，全仓 234 passed；pip check 通过。两条既有间接依赖弃用警告不影响结果。should_retry 与自写边界测试符合契约；call_with_retry 已修正返回结果、and、次数从 1 开始、提前停止与 bool 参数拒绝。
- 助手在独立子进程检查六种离线场景：success/recover 退出 0，exhausted/auth_after_503/rate_limit/timeout 退出 1；帮助退出 0，非法次数退出 2。必做 recover、exhausted --max-attempts 2、auth_after_503 的 attempts 均为 2，完整结果符合 README；单行 JSON、日文 UTF-8、stderr 提示、无 traceback、无输出文件通过。无真实模型调用，未读取 Cmder 日志，不推断学习者的完整尝试次数。
- 前轮实测 27 passed / 14 failed，当前已全部通过。前轮代码缺返回和提前结束、误用 &、计数与边界不配套的问题均已修正；这些是已解决过程，不是当前待修复代码。
- README 原先没有明确写异常消息包含 max_attempts，测试却检查了该条件。这是助手的说明遗漏，已补齐 README 并写入长期题目规则，不作为学习者漏看要求。当前实现已符合现有测试。

### 复盘反馈（助手说明，不代替独立理解确认）

1. 第 1 题：error 是固定原因字符串，不是状态码。上限 2、两次都是 503 时，report.result.error="service_unavailable"，report.result.status_code=503，report.attempts=2，sleep.calls=[0.2]。过程是“调用 1 → 等待 → 调用 2 → 返回”，最后不再等待。上限 1 时调用 1 次，sleep.calls=[]。代码现在做对了，原答把调用次数与等待次数混在了一起。
2. 第 2 题：正确实现返回第二次的 403，第三个字符串不应被读取。对 gateway.calls 的断言期望值是 [request, request]；若错误实现调用第三次，实际值是 [request, request, request]，所以断言失败。原答发现了请求次数检查方向，但把正确停止位置、期望与实际值混淆了。无需推断题目没指定的错误实现究竟如何等待，选这一项断言即可完整说明。
3. 第 3 题正确：attempts=1、sleep.calls=[]；complete 正常返回，因此调用层成功，不证明 JSON 合法或内容准确。
- 非阻塞整理建议：retry_service.py 循环后的两行返回不可达，因为最后一轮必进 else 返回；test_day20_extra.py 的 from time import sleep 未使用，被本地 sleep 变量遮盖。当前不影响验收，助手未改写学习者代码，也不把整理建议新增为完成条件。
- 实际用时按自报 2.7h 左右，难度稍高；保留开始 1412、结束 1820，不按差值推算。下次用一个已有调用序列巩固“最后结果、调用次数、等待次数”，减少同时引入的新机制，不增加补课。
- 当前代码已通过，复盘第 1、2 题待巩固；尚未标记整日收尾或提交推送。Day18 的真实对比继续留空，不要求补交。

## 学习反馈

### 再次检查反馈（2026-09-20）

- 最新全仓复测 234 passed，代码仍通过，未修改实现。
- 第 2 题已改为 403，这一处正确。还需将“期望 [request, request, request]”区分为：断言期望两次；错误实现实际调用三次。上方首次检查描述的是历史答案，不再把停止位置作为当前错误。
- 第 1 题当前 sleep.calls=[0.2]，上限 1 时为 []，等待次数已改对；上限 2 且两次 503 时，attempts 应为 2，不是 1。error 应为 "service_unavailable"，503 是 status_code。这里的 1 是等待次数，不能写成实际调用次数。
- 第 3 题仍正确。保留学习者答案、实际用时与结束时间，无需重做已正确部分。

### 最终复核（2026-09-20）

- 三题现在均正确：第 1 题已写出 service_unavailable、调用 2 次/等待 1 次、上限 1 不等待；第 2 题正确返回 403，并指出断言期望两次而错误实现实际三次；第 3 题正确区分调用成功与结构/内容正确。
- 第 1、2 题是在助手解释后由学习者修正，不表述为首次无提示独立作答；本日复盘已完成，不再要求重抄或增加题目。后续只用一个现有案例巩固。
- 两个函数和自写测试由学习者完成，助手提供脚手架、定位与讲解；代码和手动验收通过。本日按项目规则收尾、提交推送；上传结果以实际 Git 核对为准。Day18 保持原状，不补交真实对比。

- 难度与内容量：稍高
- 仍需讲解的位置：无
- 实际用时（排除中断，自行填写）：2.7h左右

- 结束时间：1820
