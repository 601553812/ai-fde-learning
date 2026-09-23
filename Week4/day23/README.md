# Day23 — 把批处理接到 FastAPI

状态：2026-09-23 已完成代码、测试与复盘验收；本日 73 项、当前本地全仓 410 项通过。下方保留原作业步骤，无需回退重现初始失败。唯一主题是 HTTP 输入 → 已有批处理 → HTTP 报告。Day22 自报 1h、简单，今天增加接口连接与独立 HTTP 边界验证，参考 90～120 分钟。不新增依赖，不调用真实模型，Day18 对比继续留空、不补交。

## 0. 按这个顺序开始

1. 在 [学习记录](./day23_notes.md) 填开始时间。
2. 在项目根运行初始检查，CMD/Cmder、PowerShell 通用：

```text
.\.venv\Scripts\python.exe -m pytest Week4/day23/tests -q
```

初始预期 **65 passed / 8 failed，退出 1**：56 项继承行为、9 项已提供的输入校验通过；两个业务 TODO 和一项自写测试造成 8 项失败。这些是作业占位，不是环境故障。实现后不用回退。

3. 读第 1～2 节，先看非测试代码，再做第 3 节 TODO。
4. 按第 4 节验证，最后填复盘和自报用时。

## 1. 两行复习（5 分钟）

当天副本 [batch_fakes.py](./code/batch_fakes.py) 中：

```python
factory = RecordingFactory({"A": ["ok"]})
gateway = factory("A")
```

第一行创建对象并运行 `__init__`，准备 gateways 和空 calls；第二行调用对象的 `__call__`，记录 A 并返回 gateway。`factory.gateways["A"]` 只是读取已有对象，不会新增 factory.calls。传递 `factory` 参数也不等于执行 `factory("A")`。此处无需重答昨天复盘。

## 2. 先理解今天的普通调用链（20～25 分钟）

阅读顺序：[api_models.py](./code/api_models.py) → [runtime.py](./code/runtime.py) → [app.py](./code/app.py)。已有服务仅在需要时查阅 [batch.py](./code/batch.py)、[summary.py](./code/summary.py)。

```text
客户端 POST /analyze-batch，发送 JSON
  → FastAPI 按 BatchRequest 检查请求体
  → get_runtime() 提供 gateway_factory 与 sleeper
  → analyze_batch(request, runtime) 今天实现
      → TaskInput 转为已有 Task
      → validate_task_ids：检查编号，只有这里的 ValueError 转 422
      → run_batch：顺序调用，每个任务保存完整报告
      → make_response：把报告整理成 dict
  → FastAPI 把 dict 转为 HTTP JSON 响应
```

请求校验失败时不会进入 analyze_batch；依赖提供函数可能执行，但创建 BatchRuntime 不会调用 factory 或模型。依赖创建与模型调用要分开看。

`request: BatchRequest` 表示接收校验后的请求对象；`request.tasks` 中每项是 TaskInput。转换成 Task 是把接口输入交给已有业务函数，不需要把 Python 对象重新 dumps/loads 一遍。

`runtime` 只是一个装着两项依赖的 dataclass。`Depends(get_runtime)` 告诉 FastAPI 调用提供函数，把返回对象作为参数传给 analyze_batch。这沿用 Week2 已学用法；可类比 Java 普通方法接收一个包含回调的对象，Python 这里由 FastAPI 负责传参，不假定你学过 Spring。

输入模型已经写好：tasks 必填、最多 10 项，允许空列表；task_id 至少 1 字符，text 长度 1～2000；max_attempts 默认 3，只接受整数 1～3。`Field(ge=1, le=3, strict=True)` 的 ge/le 是上下界，strict 避免把字符串 "1" 或布尔值当成整数。今天无需编写模型校验器。空格不自动清理，"A" 与 "a" 不同；今天不增加额外空白字符串规则。

### 三种 HTTP 结果

| 情况 | HTTP 状态 | 响应 |
|---|---|---|
| 合法批次执行完，包括其中有任务失败 | 200 | mode、tasks、summary |
| 输入模型不合法，例如 max_attempts=0 | 422 | FastAPI 默认 detail 错误列表 |
| 重复编号 | 422 | `{"detail":{"code":"DUPLICATE_TASK_ID","message":"duplicate task_id"}}` |

HTTP 200 在本接口约定中表示“批次已执行并形成报告”，不能代替逐项查看 `report.result.ok`，更不能证明模型内容正确。任务 B 的上游 403 放在 `tasks[1].report.result.status_code`；它不是整个 HTTP 响应的状态码。这是本练习的接口设计选择，不是所有批量 API 的唯一标准。

如何把已知业务错误变成 HTTP 错误，复习一个与本题不同的最小例子：

```python
if record_missing:
    raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
```

HTTPException 要 raise，不要 return；FastAPI 把 detail 放进响应 JSON。只捕获你准备处理的那一步：如果把 run_batch 也包在同一个 except ValueError 中，gateway 内部的程序错误可能被误报为重复编号。

官方补充只读 [Use HTTPException / resulting response](https://fastapi.tiangolo.com/tutorial/handling-errors/#use-httpexception) 这小段，已用 Chrome 核对。不要求读完整页或新增腾讯章节。

### 测试替换的具体含义

先看 [test_api.py](./tests/test_api.py) 的 setup_api，再看测试：

```python
app.dependency_overrides[get_runtime] = lambda: BatchRuntime(factory, sleeper)
```

字典键是原提供函数对象；值是零参数替代函数。FastAPI 会调用替代函数，得到装有测试 factory/sleeper 的 runtime。lambda 此时只返回对象，不调用 factory。测试结束清空 overrides，避免影响下个请求或测试。可以类比把 Java 方法参数替换成记录调用的对象；这里不涉及 Mockito 自动代理。

TestClient 会走请求解析、路由和响应处理，但不启动监听端口。默认会把服务器未处理的异常重新抛到测试中，所以未知 ValueError 测试用 pytest.raises；真实服务器则返回 500。今天不写全局异常处理，不暴露 debug 页面。

今天不学：async/并发、队列、流式响应、鉴权、数据库、Docker、真实模型部署、费用统计、RAG。默认 gateway 对任意编号都仅返回 `模擬結果：编号`，没有需求分析能力。mixed 测试注入 A 成功、B 403、C 503→成功，不是默认服务器的输出。

## 3. 三个 TODO（50～65 分钟）

### TODO 1：app.py / make_response

目的：让客户端收到与 CLI 一致的逐项报告和统计。

- 输入：已完成的 `list[TaskReport]`，允许空列表；无模型调用。
- 输出：新 dict，恰好包含 mode="simulated"、tasks、summary；tasks 按原顺序把每个 TaskReport 用已导入的 asdict 转为普通嵌套 dict，summary 使用已有 summarize。
- 步骤：转换每一行；取每行 row.report 组成 RetryResult 列表，调用 summarize；组装并返回三项 dict。
- 保留所有字段，包括 raw/error/status_code 中的 None；不修改 rows，不共享可变结果，不打印、不写文件。无本函数定义的业务异常或退出码。
- 验证：`test_make_response*` 两项通过；本日应 67 passed / 6 failed。

`asdict(row)` 把 dataclass 连同嵌套 dataclass 转成 dict；它不是 JSON 字符串编码。与 Day22 CLI 已用的写法相同。

### TODO 2：app.py / analyze_batch

目的：把 HTTP 请求连接到已经完成的服务，并在正确位置处理重复编号。

- 输入：校验后的 BatchRequest、BatchRuntime；保留已提供签名和路由。
- 输出：成功时返回 make_response 的 dict，FastAPI 默认 HTTP 200，即使个别任务调用失败。空批次同样返回 200 和全零汇总。
- 步骤 1：遍历 request.tasks，用每项 task_id/text 原样构造 Task 列表。
- 步骤 2：在小范围 try 中仅调用 validate_task_ids；捕获它的 ValueError，raise HTTPException(422)，detail 必须严格等于 `{"code":"DUPLICATE_TASK_ID","message":"duplicate task_id"}`。这里的 422 用 status_code 参数传入。
- 步骤 3：在上述 try/except 外调用 run_batch，传入 Task 列表、runtime.gateway_factory、request.max_attempts 和 runtime.sleeper。
- 步骤 4：把返回的 rows 交给 make_response，并返回它。
- 不打印、不写文件、不修改输入；编号重复时 factory、gateway.complete、sleeper 均零调用。run_batch 本身也会检查重复，这是保留既有服务自保行为；路由前置检查负责准确映射 HTTP 错误。
- 未预期的 ValueError/RuntimeError 原样传播，不捕获成 422，不 catch Exception。请求模型不合法的 422 由已有框架处理，不需要自己解析 JSON。
- 验证：test_api.py 的 16 项全部通过；本日应 72 passed / 1 failed。

### TODO 3：test_day23_extra.py / test_duplicate_http_request_has_no_calls

目的：独立确认重复编号不仅返回正确状态，还真的阻止整批执行。

1. 创建 `RecordingFactory({"A": ["ok"], "B": ["ok"]})` 和 RecordingSleeper。
2. 像 test_api.py 一样覆盖 get_runtime，返回包含这两个对象的 BatchRuntime。
3. 在 try 内用 `with TestClient(app) as client` 发一次 POST `/analyze-batch`，json 的 tasks 为 A/one、B/two、A/three 三项，每项字段名为 task_id/text，省略 max_attempts。
4. 断言 HTTP 状态为 422，完整 response.json() 等于上表重复编号响应。
5. 读取并断言 factory.calls、factory.gateways["A"].calls、factory.gateways["B"].calls、sleeper.calls 均为 []。读取记录不要调用 factory("A")。
6. 在 finally 中清空 app.dependency_overrides，即使断言失败也要清理。

删除 NotImplementedError 占位；该测试不返回业务值，退出码由 pytest 决定。只检查 422 检不出“先执行 A/B 后才拒绝”的实现。完成目标本日 **73 passed**。

## 4. 实现后验收（15～20 分钟）

项目根，两种 Windows shell 通用：

```text
.\.venv\Scripts\python.exe -m pytest Week4/day23/tests -q
.\.venv\Scripts\python.exe -m uvicorn Week4.day23.code.app:app --host 127.0.0.1 --port 8023
```

第三条占用当前终端，另开终端仍在项目根运行（使用 curl.exe 避免 PowerShell 别名）：

```text
curl.exe -i http://127.0.0.1:8023/health
curl.exe -i -H "Content-Type: application/json" --data-binary "@Week4/day23/sample_request.json" http://127.0.0.1:8023/analyze-batch
```

health 为 200，包含 status=ok、mode=simulated。样例 POST 为 200，A/B 两行，raw 分别为 `模擬結果：A` / `模擬結果：B`，summary 的 requests/succeeded/failed/attempts/retries 为 **2/2/0/2/0**。

再在 Chrome 打开 `http://127.0.0.1:8023/docs`，展开 POST，点击 Try it out，把 sample_request.json 内容粘入后分别验证：

- 第二项 task_id 改为 A：422，完整 detail 与重复编号契约一致。
- 恢复编号，再把 max_attempts 改为 0：422，detail 是默认错误列表。
- 输入 `{"tasks":[]}`：200，空明细、全零统计。

这三次只修改文档页面输入，不需要改样例文件。验证后在服务器终端 Ctrl+C 停止。未实现时合法 POST 会产生 500/TODO traceback，这是脚手架状态；开始阶段只要求运行初始 pytest，不要求启动未实现 API。完成后上述成功和已知错误路径不得有 traceback；未知代码错误不要求伪装成正常 JSON。

HTTP 状态与进程退出码不同：curl.exe 不加 --fail 时，收到 HTTP 422 仍可能退出 0；应看 `-i` 的状态行。pytest 全通过退出 0，有失败退出 1。CMD/Cmder 用 `echo %ERRORLEVEL%`，PowerShell 用 `$LASTEXITCODE` 检查进程退出码。

目标本日 73 passed，含本地 Day18 的当前全仓 410 passed；无新增输出文件，日文可读，三题复盘与自报用时完成后再按规则收尾提交。本次只建立学习材料，不代表学习者完成。

## 5. 来源与助手建立验证

Day22 所有 .py 与 56 项测试复制到当天目录，绝对项目导入已更新；原 test_day22_extra 改名 test_batch_inherited_extra。保留旧 CLI 演示以验证既有行为，今天只修改 app.py 和 test_day23_extra.py。新输入模型、运行依赖、16 项接口契约测试和样例由助手提供；历史代码不变，零新依赖，无真实模型请求。助手建立检查结果见根学习进度，学习者答案与时间另记。

### 最终验收（2026-09-23）

学习者完成两个函数与独立 HTTP 零调用测试，助手修正测试结束后的依赖覆盖清理；三题复盘核心结论正确。实际用时自报 1h、难度简单。本日 73 passed、全仓 410 passed；本地 HTTP 状态、逐项结果、空批次、重复编号、非法上限与日文输出通过。详细反馈见当天笔记。提交与上传状态以学习进度中的最终核对为准。

### 目录整理（2026-09-23）

- `code/` 保存接口、批处理及离线演示代码；`tests/` 保存本日 73 项自动测试；样例请求和学习文档留在 `day23/` 根目录。
- 从项目根运行当天测试：`.\.venv\Scripts\python.exe -m pytest Week4/day23/tests -q`。只改当天代码时先跑这条；本次目录和导入调整已额外跑过一次全仓回归（410 passed）。第 4 节原先要求的全仓命令已移出每日必做步骤。
- 服务器入口现在是 `Week4.day23.code.app:app`；离线演示入口如 `python -m Week4.day23.code.run_batch_demo`。第 0、4 节的建立时测试结果属于整理前历史记录，73 项契约本身未变。
