# Day 20 — 模型暂时不可用时，有限次数重试

状态：2026-09-20 已完成代码、运行验收与复盘（本日 41 passed、全仓 234 passed）；第 1、2 题经讲解后由学习者修正，三题现均正确，实际用时自报 2.7h 左右。以下保留原作业步骤，已经实现后无需重跑初始失败状态。今天只做一个主题：在 Day19 的单次调用外面控制重试。参考 90～120 分钟；全部必做操作离线，无新增依赖。Day18 的真实对比按学习者要求继续留空，不要求补交，也不是本日的前置条件。

## 0. 开始顺序（5 分钟）

1. 在 [day20_notes.md](./day20_notes.md) 填开始时间。
2. 在原项目根目录打开 CMD/Cmder。以下单行命令也适用于 PowerShell，使用根 `.venv` 的 Python 3.11：

```text
.\.venv\Scripts\python.exe -m pytest Week3/day20 -q
```

初始预期 **23 passed、18 failed，退出 1**。通过项是复制来的 19 项旧行为检查和已提供的 4 项参数校验；失败项都是本日三个 TODO 的 `NotImplementedError`，不是环境损坏。实现后不用回退代码重现初始状态。

3. 按第 1～3 节先看生产调用链和最小知识，再做第 4 节 TODO。
4. 按第 5 节测试和运行模拟，最后填写笔记复盘与自报用时。

## 1. 接着昨天的结果往前走（5 分钟）

先看 [call_service.py](./call_service.py) 的 `call_once`。沿用昨天的一个例子：如果 `complete(request)` 正常返回 `"not-json"`，`call_once` 返回 `CallResult(True, "not-json", None, None)`。

- 调用完成：`complete` 正常返回，因此 `ok=True`。
- JSON/结构合法：需要后续 `decode_requirements` 校验；`not-json` 无法通过。
- 内容正确：即使结构合法，也还要对照原文检查漏项和编造。

`ok=True` 的依据是正常返回，与是否使用测试替身无关。今天的重试只处理第一层，不用重试去修复 JSON 或证明提取准确。这里是简短复习，不重做昨天复盘。

今天在 `call_once` 外面增加一层：

```text
run_retry.main（助手提供，组装一次 request）
  → call_with_retry(gateway, request, max_attempts=3, sleeper=...)
      → call_once(gateway, request)       ← 昨天已经完成，不改
          → gateway.complete(request)   ← 每次只发送一次
          → CallResult
      → should_retry(result)            ← 今天实现：是否允许再试
      → 还有次数且允许再试时，sleeper(0.2)
      → 下一次仍传入同一个 request
  → RetryResult(result=最后一次的 CallResult, attempts=实际调用次数)
  → CLI 打印一行 JSON，设置退出码
```

例如结果顺序是 **503 → 成功**，实际过程是“调用 → 等待 → 调用 → 返回”。不会先等一次，也不会成功后等一次或再发第三次。`max_attempts=3` 表示**包括首次在内最多调用 3 次**，不是失败后额外重试 3 次。

## 2. 当天副本与文件职责

| 文件 | 来源与今天的职责 |
|---|---|
| prompt.py | 复制 Day19 的完整提示词、ModelRequest、build_request；原文保留行为不变 |
| gemini_gateway.py | 复制 Day19 的单次 HTTPX 适配器、10 秒网络阶段超时配置；不加内部重试 |
| call_service.py | 复制 Day19 已完成实现，仅清理旧 TODO 说明和未使用导入 |
| scenarios.py | 复制 Day19 的本地场景和 RAW；新 CLI 使用同一教学 RAW |
| test_call_service.py / test_call_service_extra.py / test_gateway.py | 复制 Day19 的 19 项单次调用与请求映射测试，导入改到 day20 |
| retry_service.py | 本日生产代码 TODO 1、2；返回对象和参数校验已提供 |
| test_day20_extra.py | 本日独立边界测试 TODO 3 |
| fakes.py / test_retry.py / run_retry.py | 助手提供的替身、验收测试、离线 CLI |

所有项目导入都指向本日目录，不直接依赖历史日。Day19 的真实调用 CLI 和子进程保护不在今天范围内，不复制那个入口和专属测试；历史文件保持原样。新 CLI 没有 `--live`，不会读取真实密钥或调用 Gemini。

## 3. 最小知识（20 分钟，先读再写）

### 3.1 重试是本程序的明确策略

今天只把“调用失败且 status_code 为 503”视作允许再试。这里收到的 `CallResult` 来自本日 `call_once`，字段遵守它已有的契约，不要求处理手工拼出的互相矛盾字段。

| 一次调用的结果 | 今天是否允许重试 | 原因 |
|---|---|---|
| ok=True，任何 raw | 否 | 调用已经返回，不在这一层分析内容 |
| ok=False，status_code=503 | 是，但还要有剩余次数 | 服务暂时不可用，有可能恢复 |
| 401/403 | 否 | 重发同样请求不能修正认证或权限 |
| 429 | 否 | Day19 只保留状态码，无法区分短期限流和每日配额耗尽 |
| timeout / network_error / 其余错误 | 否 | 今天的策略只覆盖 503，不把所有失败都反复发送 |

这张表是本日的保守教学规则，不表示超时、500 或短期限流在所有系统中都不能重试。外部模型请求重发会增加请求量和可能的费用；超时也不证明服务端没有处理过。今天通过离线响应序列学习控制行为。

已用 Chrome 核对官方资料，**只读下面两小段**，不用通读整页或写课程报告：

1. [Gemini API 错误表](https://ai.google.dev/gemini-api/docs/api-errors)：只看两个 429 条目和 503 条目，理解速率限制与每日配额不同，以及 503 可以等待后重试。
2. [HTTPX HTTP Transport](https://www.python-httpx.org/advanced/transports/#http-transport)：只看 connection retries 那一段。HTTPX 的 transport 重试选项处理连接错误/连接超时，不能直接代替本日对 503 的业务策略。

官方针对 503 建议指数退避。**本日固定 0.2 秒只是便于观察的离线教学间隔**，不等同生产建议，也不承诺能恢复真实服务。指数退避、随机抖动、Retry-After、总时长预算、异步、重试库、流式输出和 RAG 都不在今天范围内；不叠加新的腾讯章节。

### 3.2 传入一个函数，就是让调用者决定“怎么等待”

普通函数也可以当参数。先看一个与重试无关的小例子：

```python
def notify(send):
    send("准备好了")

notify(print)  # 传入 print 这个函数；notify 内部才调用它
```

`notify(print)` 传的是函数本身，`notify(print("准备好了"))` 则会先打印，并把 `None` 传进去，含义不同。

回到本日：`sleeper` 是一个接收秒数的可调用对象。CLI 传 `time.sleep`，你的函数调用 `sleeper(0.2)` 时就真的短暂等待。测试传 `RecordingSleeper` 对象，调用它只记录 `0.2`，不会真的等待。

`Callable[[float], None]` 表示“接收一个 float 参数、返回 None 的可调用对象”，只是类型提示，不自动执行或校验。类似 Java 把 `Consumer<Double>` 传给方法，再在方法里调用 `accept`；Python 不要求实现同一个接口，用起来也没有 `.accept()`。本日 `RecordingSleeper.__call__` 已写好，它让对象可以用 `sleep(0.2)` 这种形式调用，不要求学习所有特殊方法。

签名中的 `*` 表示后面的参数要写名字，例如 `max_attempts=2, sleeper=sleep`。调用函数内部必须使用传入的 `sleeper`，不能自行调用 `time.sleep`，否则测试替身记录不到等待。

### 3.3 返回结果与循环次数

`RetryResult` 是已提供的 dataclass：

- `report.result`：最后一次 `call_once` 返回的完整 `CallResult`。
- `report.attempts`：实际调用次数，不是配置上限，也不是额外重试次数。

例如第一次 503、第二次 403，最终必须保留第二次的 `auth_error / 403`，不能还返回第一次 503。每轮都根据**本轮**结果决定下一步。

Python `range(1, 4)` 依次产生 1、2、3，不包含 4。可以用已有的 `for` / `return` 写有限循环，不需要递归。Java 的 `for (int attempt = 1; attempt <= limit; attempt++)` 可帮助对照计数，但 Python `range` 的右边界是不包含的。

## 4. 三个 TODO（40～50 分钟）

### TODO 1：should_retry(result) — retry_service.py

目的：把重试资格单独写清楚，便于检查。

- 输入：一份符合 Day19 契约的 `CallResult`。
- 输出：只有 `ok=False` 且 `status_code=503` 时返回布尔 `True`，其他返回 `False`。此函数不考虑还剩几次，那是 TODO 2 的职责。
- 不发请求、不等待、不打印、不修改 result；不增加额外异常转换。
- 完成标准：`test_retry.py` 的 7 项 `test_retry_policy` 通过。

### TODO 2：call_with_retry(...) — retry_service.py

目的：既允许恢复，也能明确停止。

输入：同一个 gateway、ModelRequest、`max_attempts`（默认 3，只允许整数 1～3，不接受 bool）以及 `sleeper`。参数校验已提供，不需要改写；无效参数在任何调用和等待前抛 `ValueError`。

说明补正（2026-09-20）：现有测试还用 `pytest.raises(ValueError, match="max_attempts")` 检查异常消息包含 `max_attempts`，不要求整句完全一致。原 README 漏写了这一条件，只有提供的代码和测试体现；这是助手的题目说明遗漏，不作为学习者漏看要求或新的验收项。

输出：`RetryResult`，包含最后一次完整结果与实际调用次数。函数本身不设置退出码。

处理步骤：

1. 保留已提供的参数校验，从第 1 次开始，最多执行 `max_attempts` 次。
2. 每轮调用本日 `call_once(gateway, request)` 一次，接住当前返回值；不要重新构造 request，也不要绕开 call_once 直接调用 complete。
3. 若已成功、不允许重试，或已到最大次数，立即返回当前结果和实际次数。
4. 只有确定还有下一次调用时，才调用 `sleeper(WAIT_SECONDS)`，然后进入下一轮。第一次之前和最后一次之后都不等待。
5. 未预期的编程错误继续向调用者抛出；不再写一遍 Day19 的异常分类，不使用 `except Exception` 吞掉错误。CLI 的安全输出由助手提供。

完成标准：本日提供测试通过，含非默认上限 1/2、耗尽、成功提前结束、等待顺序、错误结果保留与编程错误继续抛出。只完成 TODO 1、2 后预期 **40 passed、1 failed**，剩余失败是自写测试占位。

### TODO 3：503 后变成 403 — test_day20_extra.py

这是同主题的独立边界：决定是否重试时必须检查最新结果，不能因为第一次是 503 就一直试完上限。

只修改 `test_503_then_403_stops_and_returns_latest_failure`，删除占位并写出测试：

1. `request = build_request("CSV")`。
2. 构造 `SequenceGateway([status_error(503), status_error(403), "must not reach"])`。它第一次抛 503，第二次抛 403；第三项是多余调用的检测标记，不应该被取到。
3. 构造 `sleep = RecordingSleeper()`；它的 `calls` 列表记录被要求等待的秒数。
4. 调用 `call_with_retry(gateway, request, max_attempts=3, sleeper=sleep)` 并接住结果。
5. 断言完整结果等于 `RetryResult(CallResult(False, None, "auth_error", 403), 2)`。
6. 断言 `gateway.calls == [request, request]`。
7. 断言 `sleep.calls == [0.2]`。

三项断言分别检查最新失败和实际次数、请求记录、等待次数与值。不要只执行函数、不写 assert。完成目标为本日 **41 passed**。

## 5. 实现后的测试与手动验收（15～20 分钟）

所有命令从原项目根目录运行，CMD/Cmder 和 PowerShell 通用：

```text
.\.venv\Scripts\python.exe -m pytest Week3/day20 -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m Week3.day20.run_retry --help
.\.venv\Scripts\python.exe -m Week3.day20.run_retry --scenario recover
.\.venv\Scripts\python.exe -m Week3.day20.run_retry --scenario exhausted --max-attempts 2
.\.venv\Scripts\python.exe -m Week3.day20.run_retry --scenario auth_after_503
```

| 命令场景 | report.result 的主要字段 | attempts | 退出码 |
|---|---|---|---|
| recover | ok=True，raw 为模拟 RAW，error/status_code 为 None | 2 | 0 |
| exhausted --max-attempts 2 | ok=False，raw=None，error=service_unavailable，status_code=503 | 2 | 1 |
| auth_after_503 | ok=False，raw=None，error=auth_error，status_code=403 | 2 | 1 |

`--help` 退出 0；非法参数如 `--max-attempts 0` 退出 2。TODO 未完成时运行模拟会输出 `TODO_not_completed` 并退出 2。实现后预期本日 41 passed、当前全仓 234 passed；两条既有依赖弃用警告不改变通过结果。

提交范围说明：234 项包含本地未提交的 Day18 的 11 项测试；本次仅提交 Day20 及相关文档，公开提交范围对应 223 项。本日 41 项在两种工作区中一致，历史本地文件继续保留。

CMD/Cmder 在命令后单独执行 `echo %ERRORLEVEL%` 查看退出码；PowerShell 用 `$LASTEXITCODE`。两个失败场景的退出 1 是契约要求，不代表作业失败。

最终 stdout 为一行 JSON，结构是 `{"mode":"simulated","result":{...},"attempts":2}`；提示在 stderr，不生成输出文件。注意嵌套层级：是 `result.ok`，不是顶层 ok。RAW 含日文，CLI 应保留日文文字。可以选试 success、rate_limit、timeout，但不额外要求真实 API 调用。

## 6. 收尾（10 分钟）

- 两个函数和自写测试完成；本日与历史测试通过。
- 帮助、三条必做模拟的字段和退出码符合上表，输出无敏感异常正文、无 traceback、无新结果文件。
- 填写笔记的三道复盘、自报实际用时和反馈；开始/结束时间不替代实际用时。
- 当前只是作业建立，不算学习完成；完成验收和复盘后再按项目规则提交推送。

### 助手脚手架验证记录（无需学习者另做）

- 建立前：原工作区全仓 193 passed；已有改动保留。
- 初始本日实测：23 passed、18 项 NotImplementedError 预期失败。复制的 19 项旧行为全部通过；核心 TODO 未填写。
- 全仓实测 216 passed / 18 项预期失败，历史 193 项仍通过；pip check、差异空白、UTF-8、导入隔离、敏感信息模式扫描和导航链接检查通过。
- 参考实现只在临时进程中使用：40 项提供测试及独立 503→403 边界通过；六种模拟、非默认上限、完整 JSON、日文、退出码与无输出文件已核查。帮助、非法参数和未完成 TODO 的实际子进程输出也符合契约。未调用真实模型，未将答案写入作业，不作为学习者完成证据。
