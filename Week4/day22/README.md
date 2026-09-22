# Day22 — 顺序执行多个需求任务

状态：2026-09-22 已完成代码、测试与复盘验收；本日 56 项、当前本地全仓 337 项通过。下方保留原作业步骤，无需回退重现初始失败。唯一主题是把已有单任务重试接成顺序批处理，并保留每个任务的对应关系。Day21 自报 1h、简单，今天恢复适量独立实现，参考 90～120 分钟。沿路线的模型调用与错误处理继续；Day18 真实对比留空，不补交。

## 0. 开始顺序

1. 在 [学习记录](./day22_notes.md) 填开始时间。
2. 从原项目根运行初始测试（CMD/Cmder、PowerShell 通用）：

```text
.\.venv\Scripts\python.exe -m pytest Week4/day22 -q
```

初始预期 **47 passed / 9 failed，退出 1**。47 项是 Day21 已完成行为的副本；9 项失败来自今天的三个 TODO 占位，不是环境故障。已经实现后不必回退重现。

3. 读第 1～2 节，先看非测试调用链，再做第 3 节 TODO。
4. 按第 4 节验证，再写三题复盘、自报用时与反馈。

## 1. 一个已有例子（5 分钟）

昨天“503 后成功”的任务，最终只产生一份 RetryResult：任务数 1、成功 1、失败 0、调用 2、额外重试 1。中间的 503 不另算一个最终失败任务。这是复习说明，无需重答昨日复盘。

今天给任务加上编号，例如 A、B、C，用编号把输入与最终结果对应起来。一个任务失败后，其他独立任务仍可执行，这样一次演示能同时展示成功和失败记录。

## 2. 先看非测试代码（20 分钟）

依次读 [batch.py](./batch.py) 的两个 dataclass 和函数签名 → [batch_fakes.py](./batch_fakes.py) → [run_batch_demo.py](./run_batch_demo.py)。重试细节需要时再看当天副本 [retry_service.py](./retry_service.py)。

```text
main 已提供：创建 Task 列表和 RecordingFactory
  → run_batch 今天实现
      → validate_task_ids：先检查整份列表
      → 对每个 Task：
          gateway_factory(task.task_id) 取得该任务的 gateway
          build_request(task.text) 取得 ModelRequest
          call_with_retry(...) 取得 RetryResult
          TaskReport(task.task_id, report) 保留编号与报告
      → 返回 TaskReport 列表
  → 从每行取 row.report，交给昨天的 summarize
  → 打印明细和汇总 JSON
```

`Task` 保存 `task_id` 和原文 `text`；`TaskReport` 保存同一个 `task_id` 和已有的 `RetryResult`。例如 `rows[0].report.result.ok`：先取第一行，再取该行的重试报告，最后看最终调用是否正常返回。不要把这三个对象都叫作“结果”后混用字段。

`gateway_factory` 是“传入任务编号，返回 gateway 对象”的可调用对象。生产循环只调用它一次取得对象，实际重试由该对象的 complete 执行。演示里的 RecordingFactory 预先保存各编号的 SequenceGateway，`factory.calls` 记录取对象顺序；`factory.gateways["C"].calls` 才是 C 的底层调用记录。

可以类比 Java 的 `Function<String, Gateway>`，但 Python 的 `Callable` 只是类型提示，不会自动校验返回值。RecordingFactory 的 `__call__` 由助手提供：它让 `factory("A")` 能像函数一样调用；今天无需实现特殊方法，也无需 Spring 或容器知识。

最小语法复习（不是今天的完整答案）：

```python
seen = []
for name in ["red", "blue", "red"]:
    if name in seen:
        print("already seen")
    seen.append(name)
```

这是列表成员检查，今天也可以使用已经学过的 set；不要求学新容器。重点在于**检查完整份列表后，才开始调用**。如果检查一个、执行一个，到第三项才发现重复，前两项已经执行，便不符合本日契约。

失败有两种：已知 HTTP/网络失败已由 call_once 转成 `CallResult(ok=False, ...)`，run_batch 仍追加报告并继续；未预期的 RuntimeError 等仍向外抛出，不能用 `except Exception` 把代码错误伪装成普通任务失败。

今天不新增库或官方 API，因此不增加官方文档和腾讯课程章节。只组合已学过的 dataclass、普通调用、for、列表和异常。不学并发/异步、队列、真实模型调用、持久化、计费或 RAG；没有模型内容准确性结论。

## 3. 三个 TODO（50～65 分钟）

### TODO 1：batch.py / validate_task_ids

目的：避免同一编号指向多份输入，导致报告难以对应。

- 输入：`list[Task]`；task_id 保证为非空字符串，text 保证为字符串，允许空列表。无需额外校验类型、空编号、文本内容。
- 输出：编号无重复时返回 None，不修改列表或 Task，不打印、不创建 gateway。
- 重复按字符串精确相等判断，不 strip、不改变大小写；不同编号可有相同 text。
- 异常：发现重复编号抛 `ValueError("duplicate task_id")`，消息必须完全一致，不包含输入原文。
- 步骤：建立本次已见编号集合或列表，逐个检查并记录；遇到重复抛错，合法时正常结束。
- 验证：`test_validate_*` 三项通过；本日预期 50 passed / 6 failed。

### TODO 2：batch.py / run_batch

目的：按输入顺序执行独立任务，一个已知调用失败不阻止后续任务。

- 输入：Task 列表、`gateway_factory(task_id)`、`max_attempts`、`sleeper`。本日调用方保证 max_attempts 为整数 1～3，默认 3；无需新增批处理层上限校验。其他输入遵守 TODO 1 契约。
- 输出：新 `list[TaskReport]`，每个任务恰好一行，编号和顺序与输入一致，保留完整 RetryResult。空列表返回新空列表，无 factory/complete/sleeper 调用。
- 步骤：首先调用 validate_task_ids 检查**整批**；初始化本次列表；遍历 Task，每个编号调用一次 factory，原样把 text 交给 build_request；将 gateway、request、收到的 max_attempts 与 sleeper 传入 call_with_retry；把编号与返回报告包装为 TaskReport 并追加；循环结束返回列表。
- 不因 report.result.ok=False 提前 return/break；调用失败仍占一行。不能漏传 max_attempts，不能把原文 strip；不修改输入、不保存全局列表、不打印、不写文件。
- 异常：重复编号由 TODO 1 抛出，此时不得已有任何 factory、complete 或 sleep 调用；未知异常原样向外传播，后续任务不再运行。本函数不决定 CLI 退出码。
- 验证：`test_batch.py` 全部 8 项通过；本日预期 55 passed / 1 failed。

### TODO 3：test_day22_extra.py / test_duplicate_id_rejects_whole_batch_before_calls

目的：独立验证“整批预检查”，不能只断言最后确实报错。

输入和步骤：

1. 建立 tasks：`[Task("A", "one"), Task("B", "two"), Task("A", "three")]`。
2. 建立 `RecordingFactory({"A": ["ok"], "B": ["ok"]})` 和 RecordingSleeper。
3. 用 `pytest.raises(ValueError, match="^duplicate task_id$")` 包住一次 run_batch，传入该 factory 与 sleeper。
4. 在异常检查之后，分别断言 factory.calls、A gateway.calls、B gateway.calls、sleeper.calls 均为 `[]`。

删除 NotImplementedError 占位，用以上具体输入完成测试。测试不返回业务结果，退出码由 pytest 决定。仅检查 ValueError 无法检出“执行完前两项才报错”的错误实现；调用记录能提供这个边界的证据。完成目标本日 **56 passed**。

## 4. 实现后验收（15～20 分钟）

项目根目录，两种 Windows shell 通用：

```text
.\.venv\Scripts\python.exe -m pytest Week4/day22 -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m Week4.day22.run_batch_demo --help
.\.venv\Scripts\python.exe -m Week4.day22.run_batch_demo --scenario mixed
.\.venv\Scripts\python.exe -m Week4.day22.run_batch_demo --scenario mixed --max-attempts 1
.\.venv\Scripts\python.exe -m Week4.day22.run_batch_demo --scenario duplicate
.\.venv\Scripts\python.exe -m Week4.day22.run_batch_demo --scenario empty
```

| 场景 | requests / succeeded / failed / attempts / retries | 退出码 |
|---|---|---|
| mixed 默认上限 3 | 3 / 2 / 1 / 4 / 1 | 1 |
| mixed 上限 1 | 3 / 1 / 2 / 3 / 0 | 1 |
| duplicate | error 为 duplicate task_id，无 tasks/summary | 2 |
| empty | 0 / 0 / 0 / 0 / 0，tasks 为 [] | 0 |

mixed 明细顺序 A/B/C：A 直接成功；B 为 auth_error/403，仍执行 C；C 默认第二次成功，上限 1 时为 service_unavailable/503。`tasks` 每行含 task_id 和 report，report 内有 result 与 attempts；所有既有 CallResult 字段保留。stdout 恰好一行 JSON，mode 为 simulated；stderr 是说明，日文/中文正常显示，无 traceback、无输出文件。

帮助退出 0，非法参数退出 2；未实现时输出 `{"mode":"simulated","error":"TODO_not_completed"}`、退出 2。CMD/Cmder 下一条命令运行 `echo %ERRORLEVEL%`；PowerShell 运行 `$LASTEXITCODE`。

目标：本日 56 passed；含本地 Day18 的当前全仓 337 passed。手动结果符合上表，复盘完成后按项目规则收尾并提交上传；建立作业不等于已完成。

## 5. 来源与助手验证

Day21 的所有 .py 及 47 项已完成测试复制到本日，项目导入指向 Week4.day22；原 test_day21_extra.py 改名 test_summary_inherited_extra.py。历史代码不改，旧 run_summary/run_retry 仅保留兼容演示。只需修改 batch.py 与 test_day22_extra.py。

助手提供 Task/TaskReport、RecordingFactory、CLI 和八项新契约测试；两项核心函数与一项自写测试保持占位。没有新增依赖、没有真实网络调用。助手建立验证见学习进度，不作为学习者已掌握或已完成的证据。

### 最终验收（2026-09-22）

学习者完成两个函数与独立测试，修正测试观察时意外调用 factory 的写法；三题复盘现均正确，第 2 题经逐步讲解后订正。实际用时自报 1h、难度简单。CLI 六种路径与输出契约通过，详见当天笔记。公开提交不含本地 Day18 的 11 项测试，提交范围对应 326 项。
