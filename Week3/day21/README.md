# Day21 — 汇总模型调用结果与重试次数

状态：2026-09-21 代码与运行验收通过（本日 47 项、全仓 281 项通过），复盘已收尾，第 1 题经助手逐份讲解后获学习者确认。以下保留原作业步骤，已完成实现后不需重跑初始失败状态。单一主题是把已完成的 RetryResult 列表变成运行统计，沿路线的调用记录与交付证据推进。Day20 已完成，自报约 2.7h、稍难，因此今天减少同时引入的新机制，参考 90 分钟，可在 60～100 分钟内按理解调整，不凑时长。Day18 真实对比继续留空，不补交。

## 0. 开始顺序（5 分钟）

1. 在 [学习记录](./day21_notes.md) 填开始时间。
2. 在原项目根目录运行以下命令（CMD/Cmder、PowerShell 通用，根 .venv Python 3.11）：

```text
.\.venv\Scripts\python.exe -m pytest Week3/day21 -q
```

初始预期 **41 passed、6 failed，退出 1**：41 项是复制的 Day20 已完成行为；6 项是今天两个 TODO 的 NotImplementedError，不是环境损坏。实现后无需回退重现。

3. 先读第 1～2 节的非测试调用链，再做两个 TODO。
4. 按第 4 节验收，最后填写三道短复盘、自报用时与反馈。

## 1. 用一个已有案例复习（5 分钟）

Day20 的 `test_503_then_403_stops_and_returns_latest_failure` 已复制到本日 [test_inherited_extra.py](./test_inherited_extra.py)。响应顺序 503 → 403 → 字符串，上限 3：

```text
调用 1：503 → 允许再试且还有次数 → 等待 0.2 秒
调用 2：403 → 不允许重试 → 返回；不读取第三项
```

最后 `report.result.error="auth_error"`、`status_code=403`；`report.attempts=2`，`sleep.calls=[0.2]`。最后结果、调用次数、等待次数分别是三个观察点。这里是讲解，不要求重答 Day20 复盘，也不把参考说明记成独立掌握。

## 2. 先看生产代码与最小知识（15～20 分钟）

先看 [retry_service.py](./retry_service.py) 的 `RetryResult`，再看 [run_summary.py](./run_summary.py)，最后看 [summary.py](./summary.py) 的签名。

```text
run_summary.main（已提供）
  → 每个本地场景执行 call_with_retry（已完成副本）
  → 得到一份 RetryResult，追加到 reports 列表
  → summarize(reports)（今天实现，只读取已经完成的报告）
  → 打印一行 JSON，并根据最终失败数量决定退出码
```

每份报告代表一个输入任务的最终结果，而不是每次底层调用。`report.result.ok` 是最后一次调用是否正常返回；`report.attempts` 是为这个任务实际调用了几次。503 后恢复成功的报告算一个成功任务，不再把中间 503 算成一个失败任务。

例如三个任务分别为：直接成功（1 次）、503 后成功（2 次）、503 后 403（2 次）。它们有 **3 份报告、2 个最终成功、1 个最终失败、5 次调用、2 次额外重试**。

今天只用已学过的列表、for、if、整数加法和 dict：

```python
# 无关的小例子：每次函数调用都有自己的局部计数。
def total_pages(chapters):
    total = 0
    for pages in chapters:
        total += pages
    return total
```

`list[RetryResult]` 可类比 Java `List<RetryResult>` 的元素类型提示，但 Python 标注不自动检查运行时数据。读字段用 `report.result.ok`，不是 `report["result"]`；函数最后返回的统计 dict 才用 `stats["succeeded"]` 取值。不要把对象字段与 JSON/dict 的访问混在一起。

额外重试次数 = 每份报告的 attempts 减去首次的 1 次，再相加。在当前 Day20 正常返回的协议里，每次额外调用前恰好等待一次，因此数值与等待次数相等；**报告本身没有测量等待耗时**，今天不输出耗时或费用。没有 token 用量和计价信息，也不能把调用次数当作账单。

本日不引入陌生库或新 API，不新增官方选读与腾讯章节。指数退避、异步、真实调用、token/价格、计时、日志平台、数据库、成功率百分比均不在今天范围内。`ok=True` 仍不证明 JSON 合法或内容正确。

## 3. 两个 TODO（35～45 分钟）

### TODO 1：实现 summary.py 的 summarize

目的：给演示者一份能说明运行结果与请求量的统计，不用翻每条报告。

输入：`reports: list[RetryResult]`，来自本日已完成重试函数的报告，也允许空列表；每份 attempts 为 1～3，字段遵守已有契约。无需校验手工构造的错误类型或矛盾数据。

输出：一个新 dict，恰好包含以下五个键，值都是整数：

| 键 | 含义 |
|---|---|
| requests | 报告数量，即输入任务数 |
| succeeded | 最终 result.ok 为 True 的报告数量 |
| failed | 最终 result.ok 为 False 的报告数量 |
| attempts | 所有报告实际调用次数之和 |
| retries | 所有报告额外重试次数之和，不包括各自首次调用 |

处理步骤：每次进入函数先初始化本次计数；遍历报告，累计任务数、按最终 ok 累计成功或失败、累计 attempts 和额外重试；循环结束后返回统计。空列表五项均为 0。不得修改输入列表或其中对象，不存全局累计值、不调用模型、不等待、不打印、不做内容校验。合法输入不抛异常，函数不设置 CLI 退出码。

完成标准：`test_summary.py` 的五项检查通过；此时本日预期 **46 passed、1 failed**，剩余是 TODO 2 的占位。

### TODO 2：连续汇总不串数据 — test_day21_extra.py

目的：验证统计仅属于这次传入的列表，不残留上一次统计。这是同主题的独立边界。

只实现 `test_second_summary_starts_from_zero`，删除占位。输入与调用顺序：

1. 第一份列表为 `[RetryResult(CallResult(False, None, "service_unavailable", 503), 3)]`。
2. 调用 `summarize` 并接住 first；断言完整 dict 为 `{"requests":1,"succeeded":0,"failed":1,"attempts":3,"retries":2}`。
3. 第二份列表为 `[RetryResult(CallResult(True, "not-json", None, None), 1)]`。
4. 再次调用同一个 `summarize`，接住 second；断言完整 dict 为 `{"requests":1,"succeeded":1,"failed":0,"attempts":1,"retries":0}`。
5. 再检查 first 仍等于第 2 步的完整 dict，避免返回同一个被后续修改的字典。

不预期异常、不需要网络或 monkeypatch；用上述具体输入与 assert，不能只调用函数。测试退出码由 pytest 决定。完成后本日目标 **47 passed**。

## 4. 实现后验收（15 分钟）

从项目根目录运行，两个 Windows shell 通用：

```text
.\.venv\Scripts\python.exe -m pytest Week3/day21 -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m Week3.day21.run_summary --help
.\.venv\Scripts\python.exe -m Week3.day21.run_summary --scenario mixed
.\.venv\Scripts\python.exe -m Week3.day21.run_summary --scenario empty
```

| 场景 | requests / succeeded / failed / attempts / retries | 退出码 |
|---|---|---|
| mixed | 3 / 2 / 1 / 5 / 2 | 1（有最终失败，符合预期） |
| empty | 0 / 0 / 0 / 0 / 0 | 0 |
| success（可选） | 1 / 1 / 0 / 1 / 0 | 0 |

帮助退出 0，非法参数退出 2。TODO 未完成时输出 `{"mode":"simulated","error":"TODO_not_completed"}`，退出 2。

实现后 stdout 为一行 `{"mode":"simulated","summary":{...}}` JSON；说明在 stderr，中文正常显示、无 traceback、不生成结果文件。CMD/Cmder 下一条命令用 `echo %ERRORLEVEL%` 查看退出码；PowerShell 用 `$LASTEXITCODE`。

完成目标：本日 47 passed，含本地 Day18 的当前全仓 281 passed；两个手动场景符合上表，完成笔记复盘后再收尾提交。测试通过只证明工程统计行为，不补写 Day18 真实结果。

## 5. 文件来源与助手验证

- 本日所有既有 .py 从 Day20 复制，导入统一改为 Week3.day21；包含请求、gateway、单次调用、重试、替身、场景、旧 CLI 和 41 项测试，历史代码未改。原 `test_day20_extra.py` 在本日改名 `test_inherited_extra.py`。
- 新增 summary.py、run_summary.py、test_summary.py、test_day21_extra.py；只需修改两个 TODO 文件。旧 run_retry 仅用于保留既有演示，不是今天的新作业。
- 无新增依赖、无真实模型请求；建立时本日核心实现与自写测试保留占位，现均由学习者完成。
- 助手脚手架验证结果见建立后的进度记录，不作为学习者完成证据；无需额外重做助手检查。

### 最终验收（2026-09-21）

本日 47 项、当前本地全仓 281 项测试通过；代码、CLI 和复盘已收尾，自报用时 1h、难度简单。公开提交不包含本地 Day18 的 11 项测试，提交范围对应 270 项，本日 47 项不变。第 1 题采用助手逐份讲解，保留原答，不记为无提示独立作答。
