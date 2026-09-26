# Day26 — 显式选择本地模拟或真实模型

状态：2026-09-26 已完成代码、测试与复盘收尾。唯一主题是把 Day25 的批处理 Demo 接到已有 GeminiGateway，同时保持模拟模式为默认值。参考 90～120 分钟；Day25 自报 1h、难度中。本日自写“没有密钥时拒绝真实模式”的边界测试。真实模型曾返回逐任务 `timeout`；本日不声称取得成功的模型原文。

## 0. 按顺序开始

1. 在 [学习记录](./day26_notes.md) 只填开始时间。所有命令从项目根目录执行，PowerShell 与 CMD/Cmder 都可复制。
2. 先运行脚手架检查：

```text
.\.venv\Scripts\python.exe -m pytest Week4/day26/tests -q --tb=no
```

预期 **115 passed / 2 failed，退出码 1**。两项失败分别是本日 `get_runtime("live")` 和自写测试的 TODO；其余 115 项包含从 Day25 复制的 112 项。这是待实现练习，不是已完成行为退化。完成后无需回退复现。

3. 先读第 1～2 节，再按 `code/ui.py` → `code/ui_client.py` → `code/app.py` → `code/runtime.py` → `code/batch.py` → `code/gemini_gateway.py` 看普通调用链，最后看 `tests/test_live_mode.py` 并做 TODO。
4. 实现中可重跑当天测试；完成后做第 4 节验收，填写复盘、自报实际学习时长和难度。不要把助手准备脚手架或测试替身的结果当成自己的实测。

## 1. 先用 Day25 例子复习（5 分钟）

在 [Day25 的失败汇总测试](../day25/tests/test_response_validation.py) 中，任务 A 的 `ok=True`、B 的 `ok=False`；实际成功数是 1，失败数是 1。若报告只把 `summary.failed` 写成 0，类型仍合法，但 `validate_report` 必须按任务行重算并拒绝它。今天真实模型模式返回的也必须经过相同的页面校验，不能因为 HTTP 200 就信任汇总或模型内容。

## 2. 今天需要知道的最小知识（20～25 分钟）

```text
Chrome 提交表单（默认 simulated；手动选 live 才调用模型）
  → ui_client.submit_batch：POST /analyze-batch 或 /analyze-batch?mode=live
  → FastAPI 校验 mode 和请求体
  → Depends(get_runtime)：为本次 HTTP 请求选择 gateway_factory 和 sleeper
  → run_batch：逐任务建 gateway、调用、最多重试指定次数、关闭 gateway
  → make_response：把本次 mode、任务行、汇总一同返回
  → validate_report：核对字段和汇总 → 页面显示
```

`BatchRuntime` 只是两个普通函数的组合：`gateway_factory(task_id)` 决定如何建立每个任务的调用对象，`sleeper(seconds)` 决定重试时如何等待。FastAPI 的 `Depends(get_runtime)` 会在处理请求时调用 `get_runtime`；它类似把实现传给 Java 方法，但这里由 FastAPI 从请求中读取同名 `mode` 查询参数并调用依赖函数，不能把它理解成一个必须学习的 DI 容器。默认 `simulated` 仍使用 `SequenceGateway` 和 `RecordingSleeper`；`live` 才用 `GeminiGateway` 与 `time.sleep`。

`GeminiGateway` 已封装 Gemini Interactions API：从环境变量读取 `GOOGLE_API_KEY` 或 `GEMINI_API_KEY`，发送 `ModelRequest.instructions` 与 `input`，返回模型原文。真实调用可能收费；今天只用自制日文短样例，首次手动验证选 `max_attempts=1`。密钥只能留在本机环境变量，不能写入代码、测试、笔记或截图。页面显示 `mode=live` 只表示走了真实调用路径；`ok=True` 只表示调用成功，不证明提取内容正确。Day18 尚未完成的真实对比不由本日替代。

官方参考只看 [Gemini Interactions API 的创建请求与响应](https://ai.google.dev/api/interactions-api-v1)、[Gemini 3.8 Flash 模型 ID](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash/) 的有关小节；今天的字段和调用链已在本任务单列齐，无需通读文档。今天不学异步、流式响应、API Key 管理平台、费用精算、RAG 或 Docker。Docker 本机仍未安装，容器练习留到可以实际启动验收时。

最小例子：`get_runtime("simulated")` 返回本地替身；`get_runtime("live")` 在没有密钥时必须抛 HTTP 503，在有密钥时只创建工厂和等待函数，直到任务执行才建立 `GeminiGateway`。因此空批次不应创建模型客户端。测试中的 `FakeGateway` 是替身，不会访问 Google。

## 3. 两个 TODO（50～65 分钟）

### TODO 1：`code/runtime.py` 的 `get_runtime`

目的：为真实模式选择已有调用组件，并在无密钥时给 API 安全、稳定的错误。只改 [runtime.py](./code/runtime.py) 中的 TODO；保留模拟分支。输入 `mode` 只可能是 `"simulated"` 或 `"live"`；其他值由 FastAPI 在进入依赖前返回 422。此函数不读请求正文、不发网络请求、不写文件，也没有进程退出码。

处理顺序：

1. `simulated` 返回当前 `BatchRuntime(local_gateway, RecordingSleeper())`。
2. `live` 先检查两个环境变量是否有值；都没有时抛 `HTTPException(status_code=503, detail={"code": "MODEL_NOT_CONFIGURED", "message": "Gemini API key is not configured"})`。不要把密钥或原始环境值拼进错误。
3. 有密钥时返回 `BatchRuntime`：工厂收到 `task_id` 后创建一个 `GeminiGateway()`；等待函数用 `time.sleep`。在 `get_runtime` 本身不要实例化网关，因此空批次不产生模型客户端。每个网关由已经提供的 `run_batch` 在任务结束时关闭。

类似 Java 的 `Supplier<Gateway>`：配置选择和实际创建对象是两个时间点。这里工厂虽然接收 `task_id`，当前 Gemini 网关不需要这个编号；它只是为了符合现有 `run_batch` 调用接口。完成时 `tests/test_live_mode.py` 中有密钥的替身测试应通过；缺密钥的 503 则由 TODO 2 验证。

### TODO 2：`tests/test_day26_extra.py` 的缺密钥测试

目的：独立证明真实模式在未配置密钥时返回固定错误，且不会建立网关。只改 [test_day26_extra.py](./tests/test_day26_extra.py) 的占位测试；保留原有测试。测试无返回值，pytest 成功退出 0，失败退出 1。

步骤：用 `monkeypatch.delenv("GOOGLE_API_KEY", raising=False)` 和同样写法暂时去掉 `GEMINI_API_KEY`；用 `monkeypatch.setattr(runtime, "GeminiGateway", ...)` 放一个会记录创建次数的替身；通过 `TestClient(app)` POST `/analyze-batch?mode=live`，请求为一条 `{"task_id":"A","text":"一覧をCSVで出力する。"}`、`max_attempts=1`。断言 HTTP 503、响应 `detail` **恰好**等于 TODO 1 的固定对象、网关创建次数为 0。这里不需要 `setenv`：测试的起始条件就是两个密钥都不存在。不要调用真实 API，也不要在测试中保存真实密钥。`monkeypatch` 会在测试结束后恢复环境变量。

## 4. 实现后验收（15～20 分钟）

在项目根运行当天测试，完成原有“密钥须有值”边界后应为 **118 passed**（助手在验收时补了一项空字符串测试，属于 TODO 1 已写明的条件）：

```text
.\.venv\Scripts\python.exe -m pytest Week4/day26/tests -q
```

以下本地启动步骤供学习者自行观察页面，**不作为本次助手验收要求**；用户已明确要求助手只检查代码、测试和 Cmder 日志。若自行启动，终端 1、2 分别运行：

```text
.\.venv\Scripts\python.exe -m uvicorn Week4.day26.code.app:app --host 127.0.0.1 --port 8026
.\.venv\Scripts\python.exe -m streamlit run Week4/day26/code/ui.py --server.address 127.0.0.1 --server.port 8526 --server.headless true --browser.gatherUsageStats false
```

页面需连接端口 8026；若端口被占用，先停止自己启动的旧服务，不要中断别人的服务。Chrome 打开 `http://127.0.0.1:8526`：默认 A 提交显示 `mode=simulated`、原有 `模擬結果：A` 和 `1/1/0/1/0`。另用当天测试替身检查 live 结果标签及错误，不把替身输出称为真实模型结果。若本机密钥环境变量可供终端进程读取，再手动选 `live`、`max_attempts=1`、仅 A 的自制短句提交一次，记录页面是否显示 `mode=live`、返回原文或明确错误，以及实际任务/调用数；不要因为失败反复请求。若密钥未传到服务进程，记录 503 并停止，不把 live 标为已验证。最后 Ctrl+C 停止本日两个服务。

代码与测试检查还包括：空 A 不发请求、非法 mode 返回 422、模拟模式仍不访问外网；模型原文的内容准确性不属于本日代码通过的证据。完成后填 [学习记录](./day26_notes.md) 并交助手做最终检查。Cmder 日志只用于核对命令、报错和修正过程，不用于计算实际学习时长。

## 5. 助手建立记录

- 从 Day25 复制当天所需代码、测试与脱敏样例，替换为 `Week4.day26` 包路径；复制后的原有 **112 passed**，历史文件未改。
- 已提供模式选择页面、HTTP 路由参数、响应 `mode` 标识、页面响应校验兼容两模式、真实模式较长的客户端等待上限、网关关闭和离线测试。仅 `get_runtime` 与独立缺密钥测试保留核心 TODO。建立状态与学习者完成状态分开记录。
- 助手建立检查：当天 **115 passed / 2 项预期 TODO 失败**；因新增当天包，助手额外跑全仓得 **728 passed / 同 2 项失败**，其余历史测试通过。`pip check` 与已跟踪文件 `git diff --check` 通过。没有发起真实模型调用或浏览器人工验收。
- 当前验收（2026-09-26）：学习者实现后原 117 项通过；按 TODO 1 已写明的“有值”条件，助手补测两个环境变量存在但值为空字符串的情况，当前 **117 passed / 1 failed**。Chrome 默认模拟模式的 A 提交显示 `simulated`、`模擬結果：A` 和 `1/1/0/1/0`。学习者报告一次真实模式任务显示 `timeout / None`；助手未重复付费调用，也不能将此记为真实模型成功返回。详细反馈见当天笔记。
- 最终收尾（2026-09-26）：学习者修正无密钥、空字符串密钥和单个有效密钥的选择逻辑；当天 **118 passed**，助手全仓 **731 passed**，`pip check` 与差异检查通过。用户指定本次只按代码、测试和 Cmder 日志验收；此前页面观察仅为历史记录。学习者自报用时 `2h-`、难度中；复盘第 2 题模拟原文已订正，live 的固定统计由助手补准，不记为学习者独立写出。Cmder 命令过程、错题和真实调用限制见当天笔记。
