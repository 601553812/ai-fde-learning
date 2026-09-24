# Day24 — 给批处理 API 加一个浏览器页面

状态：2026-09-24 已完成代码、测试、复盘与验收；本日 91 项通过。下方保留原作业步骤，无需回退重现初始失败。唯一主题是用 Streamlit 连接已有 HTTP API，形成可操作的本地 Demo。参考 90～120 分钟；Day23 自报 1h、简单，今天增加表单输入处理和客户端错误边界。后端仍是明确标注的模拟服务，不证明模型提取效果。Day18 真实对比继续留空，不补交。

## 0. 按这个顺序开始

1. 在 [学习记录](./day24_notes.md) 填开始时间。
2. 在项目根运行初始检查（CMD/Cmder、PowerShell 通用）：

```text
.\.venv\Scripts\python.exe -m pytest Week4/day24/tests -q
```

初始应为 **76 passed / 15 failed，退出 1**。73 项继承测试和 3 项已提供页面测试通过；两个函数 TODO 和一项自写测试导致 15 项失败，这是练习占位。实现后不必回退重现初始失败。

本机已在根 Python 3.11 `.venv` 安装并验证 Streamlit 1.64.0，依赖要求已写入根 requirements-dev.txt。另一台机器按根 README 安装依赖即可。

3. 先读下面第 1～2 节和非测试代码，再看测试、做 TODO。
4. 完成后按第 4 节运行两个服务，在 Chrome 操作页面，最后填写复盘与自报用时。

## 1. 用昨天的一个例子复习（5 分钟）

当天副本 [test_api_inherited_extra.py](./tests/test_api_inherited_extra.py) 输入 A/one、B/two、A/three：重复编号导致 HTTP 422，factory、两个 gateway 和 sleeper 都应零调用。它在执行前拒绝整批。

另一种情况：编号都合法，执行后 B 上游返回 403。整个接口返回 HTTP 200，B 的 `report.result.ok=False`、`status_code=403`。200 表示批次报告已经生成，不表示每个任务成功。今天页面必须保留这个区别。无需重答昨天复盘。

## 2. 最小知识与调用链（20～25 分钟）

阅读顺序：[ui.py](./code/ui.py) 的 main → [ui_client.py](./code/ui_client.py) 两个函数签名 → ui.py 的 render_report。后端仅查阅当天 [app.py](./code/app.py)，不修改历史日代码。

```text
Chrome 页面，输入 A/B 后点击提交
  → Streamlit 重新执行 ui.py（本地 Python 进程，端口 8524）
  → submitted 为 True，进入 if
  → build_payload：文本 → 请求 dict
  → submit_batch：HTTP POST 到端口 8024
  → FastAPI /analyze-batch → 昨天已完成的批处理
  → HTTP JSON 报告 → render_report → 页面结果
```

两个服务是两个 Python 进程。HTTP 请求由 Streamlit 的 Python 代码发出，不是你写浏览器 JavaScript 发出。FastAPI 提供数据，Streamlit 提供输入框和结果展示；关掉 FastAPI，页面仍可打开，但提交会连接失败。不会直接调用另一天的 app 或模型。

### 今天只需掌握这些 Streamlit 用法

- `st.text_area(...)` 显示多行输入框，返回当前字符串；`st.selectbox(...)` 返回选中的值。
- `with st.form("requirements"):` 把输入放在一个表单内；提交时一起送回 Python，并触发脚本重跑。`enter_to_submit=False` 使表单用按钮提交。
- `st.form_submit_button(...)` 返回布尔值；这次运行因提交触发时为 True。网络调用必须放在 `if submitted:` 内，否则初次打开就会调用。
- `st.text(...)` 按文本显示原始输出；`st.json(...)` 展示报告；`st.error(...)` 显示已知输入/连接错误。逐任务失败由 `st.warning` 展示，不能一律显示成功。

一个与作业不同的最小例子：

```python
with st.form("greeting"):
    name = st.text_input("名前")
    submitted = st.form_submit_button("表示")
if submitted:
    st.write(f"こんにちは、{name}")
```

可类比 Android 的“读输入→点击提交→展示结果”，但 Streamlit 通常重跑脚本，不是给按钮注册一个 Java `OnClickListener`。普通局部变量也不会自动成为跨次运行保存的状态。今天结果只在本次提交分支显示；不做历史记录、刷新恢复或会话状态。表单也不等于防重复提交：每次点击都可以产生新的请求。

官方补充只读 [st.form 的说明与第一个例子](https://docs.streamlit.io/develop/api-reference/execution-flow/st.form) 和 [Using forms 的开头](https://docs.streamlit.io/develop/concepts/architecture/forms)。已通过官方文档检索核对；Chrome 控制连接不可用，未声称用 Chrome 完成核对。不新增腾讯章节，不要求另交读书报告。

### HTTP 客户端：沿用已经学过的顺序

`client.post(..., json=payload)` 自动把 dict 编码为请求 JSON。随后 `response.raise_for_status()` 检查 HTTP 错误，再 `response.json()` 解码响应。返回的仍是 dict，不是 JSON 字符串。

ui.py 已创建并关闭 `httpx.Client`，指定本地 base_url；你只传路径 `/analyze-batch`。`trust_env=False` 使本地连接不受系统代理环境变量影响。每次请求用 5.0 秒超时；HTTPX 的超时约束网络阶段，并非严格的整个业务运行总时限。

`httpx.HTTPStatusError` 代表错误 HTTP 状态；`httpx.RequestError` 代表请求没能正常完成（包括连接、读取超时等）；JSON 解码的 `ValueError` 单独处理。后端重试上游 503 与页面重试整个 POST 是两回事：今天页面只 POST 一次，避免重复执行一批任务。不要捕获所有 Exception。

今天不学：React/HTML/CSS、async/并发、Session State、缓存、上传文件、真实模型接入、Docker、部署、RAG。页面只接收固定本地 Day24 API 的响应结构；处理不合法 JSON，但暂不增加一套完整响应 Schema 校验。

### 再看测试替身

[test_ui_client.py](./tests/test_ui_client.py) 的 RecordingClient 是普通对象，其 post 方法记录路径、dict、超时，再返回预先准备的 httpx.Response 或抛异常。submit_batch 调用的是传入对象的 post；不是 Mockito，也没有真实网络。

已提供 [test_ui.py](./tests/test_ui.py) 使用 Streamlit AppTest 运行页面脚本、模拟提交并替换函数，验证页面连接和展示。它不启动 Chrome，不能替代浏览器视觉验收。今天无需学习或编写 AppTest API。

## 3. 三个 TODO（50～65 分钟）

### TODO 1：ui_client.py / build_payload

目的：把两个输入框变成昨天 API 接受的请求。

- 输入：两个字符串 text_a/text_b；max_attempts 已由页面限制为整数 1、2、3，这是本函数前置条件，不要求新增该参数校验。
- 顺序：先分别 strip 去首尾空白；A 为空先报错；再检查 A/B 清理后的长度；创建 A 任务，B 非空才追加 B；最后返回 dict。
- A 必填，空时抛 `DemoError("需求 A 不能为空")`。
- 清理后的每段最多 2000 字符，等于 2000 允许；超过时分别抛 `DemoError("需求 A 不能超过 2000 字符")` 或 B 对应消息。内部换行/空格原样保留，只有首尾被清理。
- 输出恰好含 tasks 和 max_attempts；tasks 中 A 在前、B 在后，每项只有 task_id/text。编号固定大写 A/B，省略空 B；max_attempts 原样传入。
- 不网络调用、不打印、不写文件；每次创建新的 dict/list。无进程退出码。
- 示例：`build_payload(" one ", " \n ", 2)` → `{"tasks":[{"task_id":"A","text":"one"}],"max_attempts":2}`。
- 验证：7 项 payload 测试通过，本日 **83 passed / 8 failed**。

### TODO 2：ui_client.py / submit_batch

目的：调用 API，给页面可展示的报告或已知错误。

- 输入：已创建的 client、build_payload 生成的 payload（测试也会直接传合法空批次）；不在本函数创建/关闭 client。
- 步骤：只调用一次 `client.post("/analyze-batch", json=payload, timeout=5.0)`；先 raise_for_status，再解码 JSON；返回解码结果，不修改 payload 或逐项报告、不重算汇总。
- HTTPStatusError → 抛 DemoError，消息为 `接口请求失败（HTTP N）`，N 取 `exc.response.status_code`。例如 422：`接口请求失败（HTTP 422）`。不用把响应正文或原异常全文带给页面。
- RequestError → `DemoError("无法连接接口或请求超时，请检查本地 API 服务")`。
- 仅在 JSON 解码步骤捕获 ValueError → `DemoError("接口未返回合法 JSON")`。500 即使正文不是 JSON，也要先报 HTTP 500，而不是 JSON 错误。
- HTTP 200 中有 ok=False 的任务仍返回完整报告。页面已会按任务显示警告。
- 未预期程序错误原样传播；不 catch Exception，不重试、不打印、不写文件。函数自身没有进程退出码；已知错误由页面捕获显示。
- 验证：另外 7 项 submit 测试通过，本日 **90 passed / 1 failed**。

### TODO 3：tests/test_day24_extra.py

独立检查“HTTP 200 中的失败任务不能被丢掉或当成整个请求失败”。删除占位，并按下列输入完成测试：

1. body 为 `{"mode":"simulated","tasks":[{"task_id":"B","report":{"result":{"ok":False,"raw":None,"error":"auth_error","status_code":403},"attempts":1}}],"summary":{"requests":1,"succeeded":0,"failed":1,"attempts":1,"retries":0}}`。
2. 使用已导入的 `response(body=body)` 创建 HTTP 200 响应，交给 RecordingClient。
3. payload 为 `{"tasks":[{"task_id":"B","text":"確認"}],"max_attempts":1}`。调用 submit_batch。
4. 断言返回值完整等于 body；再断言 `client.calls` 完整等于 `[('/analyze-batch', payload, 5.0)]`。

完整比较会检查失败明细和汇总都保留；调用记录会检查请求只有一次且参数正确。测试无需返回值；pytest 全通过退出 0，有失败退出 1。完成目标 **91 passed**。

## 4. 实现后验收（15～20 分钟）

在项目根运行当天测试，不要求全仓：

```text
.\.venv\Scripts\python.exe -m pytest Week4/day24/tests -q
```

同样在项目根，终端 1 启动 API：

```text
.\.venv\Scripts\python.exe -m uvicorn Week4.day24.code.app:app --host 127.0.0.1 --port 8024
```

终端 2 启动页面（两种 Windows shell 通用，整行复制）：

```text
.\.venv\Scripts\python.exe -m streamlit run Week4/day24/code/ui.py --server.address 127.0.0.1 --server.port 8524 --server.headless true --browser.gatherUsageStats false
```

Streamlit 的启动器接收脚本路径，这是框架入口形式；内部项目导入仍用完整 `Week4.day24.code` 路径。不要直接 `python ui.py`。

在 Chrome 打开 [本地 Demo](http://127.0.0.1:8524)，依次检查：

| 操作 | 预期 |
|---|---|
| 初次打开，不点击 | 可见模拟模式说明、两个输入框和提交按钮；不请求 /analyze-batch |
| A 默认值，B 留空，上限选 1，提交 | 一个 A；raw 为 `模擬結果：A`；汇总 1/1/0/1/0 |
| B 填 `文字コードを確認する。`，提交 | A/B 两个结果；汇总 2/2/0/2/0，日文可读 |
| A 清空或只留空格，提交 | `需求 A 不能为空`；API 终端不新增 POST 访问记录；本次无成功报告 |
| A 粘贴超过 2000 字符，提交 | 长度错误；不请求 API |
| 恢复合法 A，终端 1 Ctrl+C 停止 API，再提交 | 连接/超时提示，不出现旧成功报告或页面 traceback |
| 重启终端 1 的 API，再提交 | 恢复正常显示，页面服务无需重启 |

超长文本可用编辑器重复粘贴生成，无需保存文件。编号由页面固定分配，所以页面不额外增加重复编号输入。后端 422 和 HTTP 200 带失败任务由自动测试覆盖；默认模拟服务只返回成功，不把测试注入的失败声称为真实模型结果。

已知错误应显示页面消息，不能显示完整异常堆栈；不产生业务输出文件。完成后两个终端各 Ctrl+C 停止。启动服务持续占用终端，不把服务运行时没有退出当成失败。

填好笔记三题、自报用时和难度后交给助手验收，再按项目规则收尾提交。脚手架建立和助手参考验证不等于学习者完成。

## 5. 来源与助手建立验证

- 从 Day23 复制 code、tests 中的 Python 模块及样例；73 项既有行为保留，全部项目导入改为当天路径，历史代码未改。原自写测试改名 test_api_inherited_extra.py。
- 新增 ui.py、ui_client.py 和三份测试文件。核心两函数与独立测试仍是 NotImplementedError，不提供落盘答案。
- 新依赖 Streamlit 已安装、可导入；pip check 通过。新页面由助手提供。Chrome 连接不可用，浏览器视觉与手动操作验收未完成；AppTest 验证另记，不冒充 Chrome 实测。
- 实际建立结果与进程内参考验证见根学习进度；学习者不需要重做助手检查。

### 最终验收（2026-09-24）

学习者完成两个函数及 HTTP 200 失败行的独立测试；助手修正测试请求字段 `report` 为 `text`，保留测试的主要断言。Day24 91 passed、pip check 通过；Chrome 中 A、A+B、空白/超长 A、日文结果及无旧成功报告通过。真实关闭端口验证连接错误提示，AppTest 验证错误后再次提交可恢复。用户正在运行的 API 未被停掉，停服/重启这一项 Chrome 手动动作未执行，相关代码路径由等价隔离检查覆盖。三题复盘经订正后核心结论正确，第 2 题的 HTTP 500 页面文字由助手补准；实际用时自报 1h、难度中。详细记录见当天笔记与根学习进度。
