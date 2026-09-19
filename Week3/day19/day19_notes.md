# Day 19 学习记录 — 模型调用失败时返回什么

状态：已完成；日期：2026-09-19。本日必做验收通过，可选真实调用超时如实记录。

## 学习开始

- 开始时间：1202
- 环境确认：原项目根目录、根 .venv；按 README 第 0 节先检查脚手架。

## 本日学习目标（无需提前作答）

- 沿 request → complete → CallResult 解释一次调用的成功或失败。
- 区分网络超时、HTTP 错误响应和其他网络错误；只调用一次，不用失败结果冒充成功。

## 运行结果（执行后填写，可结合 Cmder 日志核查）

- 初始测试：助手核对 Cmder：5 passed、15 failed，均为预期 TODO 失败，退出 1。
- 实现后本日测试 / 全仓测试：Cmder 为 20 passed / 193 passed，退出 0；助手全仓复测也是 193 passed，pip check 通过。

| 本地模拟命令 | ok | error | status_code | 退出码 |
|---|---|---|---|---|
| --scenario success | True | None | None | 0 |
| --scenario timeout | False | timeout | None | 1 |
| --scenario unavailable | False | service_unavailable | 503 | 1 |

- 真实调用（可选，未执行可留空；不可填写模拟结果）：Cmder 记录 --live 返回 mode=live、ok=False、raw=None、error=timeout、status_code=None；下一条 CMD_META 确认退出 1。没有取得模型文本，不能评价内容效果；本日可选项失败不影响必做验收。本轮助手未再次调用 API。

## 学习后复盘

以下题目都有给定条件，不需要先成功调用 Gemini；用 1～2 句或字段值回答。

1. 在 call_service.py 中调用 `call_once(gateway, request)`，假设 gateway.complete 抛出 ReadTimeout，没有收到 HTTP 响应。预期返回对象的 ok、raw、error、status_code 分别是什么？

   回答：CallResult(ok=False, raw=None,error="timeout",status_code=None)

2. 在 test_day19_extra.py 中，FakeGateway 抛出 ConnectTimeout。假设错误实现把 `except httpx.RequestError` 放在 TimeoutException 前面，并返回 error="network_error"：实际会进入哪一个 except？你对完整返回值的断言会通过还是失败？

   回答：会进入RequestError,会失败

3. 在 test_day19.py 的 test_success_preserves_raw_and_calls_once 中，FakeGateway 正常返回字符串 `"not-json"`。为什么 call_once 仍应该返回 ok=True？这个 True 能否说明需求提取内容正确？

   回答：因为raw是通过response注入的 不能说明提取正确

## 错题本与验收反馈

### 助手验收（2026-09-19）

- 两个函数及自写测试均已完成；HTTPX 的 TimeoutException 在 RequestError 前面，HTTPStatusError 读取响应状态码；未匹配的 ValueError 会传给调用者，不会被误报成网络错误。
- 全仓 193 passed，包含本日 20 项；pip check 通过。两条原有间接依赖弃用警告未影响结果。手动检查六种模拟场景、帮助及非法参数，退出码 0/1/2、单行 JSON、日文输出、stderr 提示、无输出文件均通过。
- 自写测试能拒绝错误返回值和重复调用：分别临时制造 network_error 及两次 calls，两个错误都被断言发现。临时替换仅在验证进程中生效，未修改学习者代码。
- Cmder 三轮本日测试依次为 15 failed / 5 passed → 1 failed / 19 passed → 20 passed；随后全仓 193 passed。中间一次失败来自导入 urllib3 的同名 RequestError，已修正为 httpx.RequestError；未把初始脚手架失败记成学习错误。
- 日志提示符时间只用于定位命令，不推算学习时长；即使初始检查早于笔记开始时间，仍保留学习者自填开始 1202、实际用时 1h+、结束 1316。
- 复盘第 1、2 题正确。第 3 题“不保证提取正确”的结论正确；助手补充原因：complete 正常返回了字符串，本层只检查调用是否成功，所以 ok=True。不是“因为使用了测试注入才为 True”；即使真实模型返回 not-json，本层也会为 True，后续结构/内容校验才能继续判断。保留原答，补充不当作学习者独立表达的证据，无需重抄。
- 下次只用一次现有调用简短巩固“请求完成 / JSON 合法 / 内容正确”三个不同检查点，再按路线继续，不追加补课。Day18 的留空结果保持不变。

### 典型错误记录（本次已修正）

- 错误导入：`from urllib3.exceptions import RequestError`。
- 正确导入：`from httpx import RequestError`。
- 原因：httpx.ConnectError 继承 httpx.RequestError，不继承 urllib3 的同名类；except 匹配异常类的继承关系，不按名称匹配。
- 最小核查：`issubclass(httpx.ConnectError, httpx.RequestError)` 为 True。测试里的 private mock detail 是模拟异常文本，不是真实服务故障。

## 学习反馈

- 难度与内容量：中
- 仍需讲解的位置：无
- 实际用时（排除中断，自行填写）：1h+

- 结束时间：1316
