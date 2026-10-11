# Day34 — 把资料问答接到真实 Gemini，并人工核查依据

状态：已完成本日学习与验收（2026-10-12，93 passed；真实 A/B 已由授权的 Cmder 日志核实，人工核查由助手补录）。资料编号与 HTTP 回调概念仍需巩固，不把助手讲解记为独立掌握。唯一主题是 **Gemini 问答适配与结果核查**。参考 90～120 分钟；本次学习者自报实际用时 2h+、难度难，后续缩小同时引入的概念范围。下方 TODO 和失败结果保留为原任务与历史检查过程，当前结论见第 12 节。

## 0. 今天按这个顺序执行

1. 在 [学习记录](./day34_notes.md) 填开始时间，复盘留到最后。
2. 在**仓库根目录**执行初始检查。下面命令均为单行，PowerShell、CMD/Cmder 通用，使用根 Python 3.11 `.venv`：

   ```text
   .\.venv\Scripts\python.exe -m pytest Week5/day34/tests -q
   ```

   原始脚手架实测 **75 passed / 17 failed**（2026-10-11 建立记录）。原因是 `build_gemini_payload()`、`extract_answer()` 和独立测试尚未实现；不是环境坏了。继承的 69 项仍通过。已经实现后不必还原初始状态；2026-10-12 补强一项原契约测试，当前目标及检查结果见末尾记录。
3. 先读下方普通函数调用链和最小知识，再读 `code/gemini_gateway.py`。此时不要求先读测试。
4. 运行只预览的入口，观察真正发送的资料，再依次做三个 TODO。
5. 当天离线测试全部通过后，再运行 A、B 的真实单次调用并填人工核查记录。C 的零调用可以离线验证；不重复付费调用来凑次数。

本日从 Day33 复制所需代码和 69 项测试至 `Week5/day34/code/`、`tests/`，导入和替换路径全部指向当天。Gemini HTTP 外壳参考 Day26，改用本日 `ModelRequest`；固定规则、检索、字符预算、无资料零调用和编号检查行为保留，历史目录不改。没有新增第三方依赖。

## 1. 先复习一个现有例子

资料写着“返品期限は30日”，模型返回“返品期限は90日です。[1]”：编号存在，所以 `review_qa_result()` 返回 `[]`；但“90日”与原文冲突。今天要记录**模型原回答、真正发送的原文、人工判断**，把这三者放在一起核对。

这里的 citation id 指回答中 `[1]` 这样的**资料编号**。`build_context()` 在本次实际发送的第一块原文前加 `[1]`，它对应 `context.chunks[0]`；第二块才是 `[2]`。资料编号每次组装上下文重新从 1 排起，不是原文的 `chunk_index`（后者从 0 起，按文档内切块顺序记录）。

B 中有一块资料实际发送，所以合法资料编号只有 1。但模型看到 `[1]` 不代表一定会把 `[1]` 写进回答。示意回答“資料からは回答できません。”没有任何 `[数字]`，因此 `extract_citation_ids(answer)` 得到 `[]`，随后检查返回 `['missing_citation']`。这不意味着 `context.chunks` 为空：资料仍然发送了，只是回答没有写编号。

人工核查另看原文是否能回答送料问题。本例原文只有期限和开封条件，未写送料承担方，拒答符合已有规则。如果问的是返品期限，原文已写明 30 日，模型却仍说无法回答，才是资料足以回答却未回答。两种拒答文字都可以没有编号，因此 missing_citation 只表示回答缺编号，不能说明原文是否已提供问题的答案。当前编号检查对所有 generated 文字检查编号，没有拒答例外。此次只补解释，不改变编号检查实现或验收要求。

## 2. 先看普通函数调用链

今天仍使用 `qa_service.py` 中已经完成的函数：

```text
answer_question(chunks, question, 2, 500, gateway)
  → retrieve_chunks：按关键词选出片段
  → build_context：只留下预算内资料，并编号
  → 无资料：返回 no_context，结束，不调用 complete
  → 有资料：build_qa_request → ModelRequest(instructions, input)
  → gateway.complete(request)
      → build_gemini_payload：内部对象 → HTTP 请求 dict（TODO 1）
      → client.post：发送一次 HTTP POST（已提供）
      → raise_for_status → response.json（已提供）
      → extract_answer：响应 dict → 原回答 str（TODO 2）
  → QAResult(status="generated", answer=原回答, context=实际资料)
  → review_qa_result：另行检查编号
  → 人工核对回答与原文
```

原先传入 `RecordingGateway`，它返回人为固定文字；现在传入 `GeminiGateway`，相同调用点执行 HTTP。类似 Java 中把有相同 `complete` 方法的另一个实现传给调用者。类比边界：Python 这里没有强制声明 Java `implements`，本日 `GeminiGateway` 也不必继承基类；它提供所需方法即可。

`ModelRequest.input` 已是含 `question/context` 的 JSON **字符串**。HTTP 外层的 body 是 **dict**，由 `httpx` 的 `json=payload` 编码。嵌套层次是“HTTP 请求字典中有一个字符串字段”，不是把 `input` 改成 dict，也不是再对这个字符串调用 `json.dumps()`。

## 3. 今天只需这些知识

### 请求字段的对应关系

| 本地值 | HTTP 字典中的键 | 作用 |
|---|---|---|
| 传入的 `model` | `model` | 本次选用的模型 |
| `request.instructions` | `system_instruction` | 固定回答规则 |
| `request.input` | `input` | 原问题与真正发送的资料，保持原字符串 |
| `False` | `store` | 不为后续 `previous_interaction_id` 存储本次互动 |

今天是独立单次问答，不增加聊天历史、工具或后台请求。`store=False` 是该 API 的互动存储开关，不代表全部服务数据处理规则。官方接口和模型名已在 Chrome 核对：[Interactions 概览](https://ai.google.dev/gemini-api/docs/interactions-overview)、[请求与响应结构](https://ai.google.dev/api/interactions-api#CreateInteraction)。只参考上述字段与下方 `model_output`，不用通读整页，也不新增腾讯章节读书报告。

### HTTP 200 后还要从响应中找到回答

供应商响应示例（**示意数据，非真实调用证据**）：

```json
{
  "status": "completed",
  "steps": [
    {"type": "thought"},
    {"type": "model_output", "content": [
      {"type": "text", "text": "返品期限は"},
      {"type": "text", "text": "30日です。[1]"}
    ]}
  ]
}
```

这里的 `data["status"]` 属于供应商；`result.status` 属于我们的 `QAResult`，是不同对象中的同名字段。供应商 `completed` 表示互动完成；本地 `generated` 表示网关返回文字，两者都不证明“30日”有依据。

`steps` 是列表，每个 step 是字典；step 中的 `content` 又是片段列表。只使用**最后一个 `type="model_output"` 的步骤**，只拼接它里面 `type="text"` 的文字，按原顺序、不插分隔符。thought 或 image 不是本日要展示的回答。

今天需要的小语法，先看与作业不同的数据：

```python
record = {"name": "sample"}
record.get("count", 0)       # 缺键时得到 0；不是往字典里写入 count。
list(reversed([10, 20, 30])) # [30, 20, 10]，不改原列表。
"".join(["保存", "期限"])   # "保存期限"，不自动加空格。
" \n".strip() == ""         # True；strip 返回新字符串。
```

类似 Java 遍历 List、访问 Map、拼接 String，概念已有基础；Python 的写法不同。验证空白时可以用 `strip()`，**返回回答时要保留原首尾空白**。

### 用 HTTP 替身验证转换代码

`httpx.MockTransport(handler)` 让 `client.post()` 调用本地 `handler(request)`，不会上网。这次与 `RecordingGateway` 的替换位置不同：`complete()`、两个新函数和 HTTP 状态检查仍实际执行，仅把最底层发送网络请求换成本地函数。相当于 Java 测试中把 HTTP 传输层替换成假的返回方；不是 Mockito 的完全等价 API。

最小形状，返回数据先不涉及本日答案：

```python
def handler(http_request):
    return httpx.Response(200, json={"message": "sample"})

transport = httpx.MockTransport(handler)
```

真正测试要把 `transport` 传进 `GeminiGateway(..., transport=transport)`。假密钥只用 `fake-test-key`。`http_request` 是 HTTP 请求对象，不是内部 `ModelRequest`；`json.loads(http_request.content)` 才是它真正发送的外层字典。

今天不学：Embedding/向量库、语义检索、流式、异步、重试、批处理、完整 SDK、多轮记忆、工具调用、新 Web 页面或 Docker。关键词检索局限仍保留，不能把无命中当成模型拒答。

## 4. 先预览，仍不联网

```text
.\.venv\Scripts\python.exe -m Week5.day34.code.run_live_qa --case A
.\.venv\Scripts\python.exe -m Week5.day34.code.run_live_qa --case B
.\.venv\Scripts\python.exe -m Week5.day34.code.run_live_qa --case C
```

三个命令均退出 0、各输出一行 UTF-8 JSON。无需密钥，也不执行两个 TODO，不写文件。`instructions` 是规则，`input.question` 是问题，`input.context` 是已经编号的实际资料；`would_call_model` 在 A/B 为 true，C 为 false，`gateway_calls` 始终为 0。

资料来自 `cases.py` 的自制 FAQ：`返品期限は30日です。\n開封済みの商品は返品できません。`。问题刻意用空格保留已有按词项检索方式：

| case | 原问题 | 检索与人工核查目标 |
|---|---|---|
| A | `返品 期限` | 原文有期限 30 日；回答应有据并引用 `[1]` |
| B | `返品 送料` | “返品”使资料命中，但原文未写送料由谁承担；应按规则拒答 |
| C | `駐車場` | 无命中；应用返回 no_context，模型没有被询问 |

B 与 C 的区别：B 是**已发送资料但资料没有答案**，C 是**没有资料可发送**。B 若模型遵守规则返回固定拒答且不含编号，旧编号检查会报告 `missing_citation`；保留这个结果并解释检查的局限，不在今天增加拒答例外。

## 5. TODO 1：转换请求字典（约 10～15 分钟）

修改 `code/gemini_gateway.py` 的 `build_gemini_payload(request, model)`。

- 目的：让已有内部对象能传给官方 HTTP 端点。
- 输入：`ModelRequest` 与非空模型名 `str`；模型/密钥配置校验由已提供的构造函数处理。
- 输出：**恰好**包含第 3 节四个键的 `dict`；规则、输入原字符串和模型名原样保留，`store` 为 `False`。
- 不改变原对象，不读环境，不发送请求，不再编码 `request.input`；合法输入不抛异常。
- 完成标准：请求字典测试通过，HTTP 替身看到同一个完整字典。

```text
.\.venv\Scripts\python.exe -m pytest Week5/day34/tests/test_gemini_gateway.py -q
```

原始脚手架中，本文件初始 1 passed / 16 failed；只做 TODO 1 后 5 passed / 12 failed，剩余是文字提取占位。2026-10-12 新增类型筛选契约测试后，本文件完成目标为 18 passed；不要求还原已完成的部分。

## 6. TODO 2：从响应取出最后的原回答（约 20～30 分钟）

仍只修改 `code/gemini_gateway.py`，实现 `extract_answer(data)`。

- 输入：供应商响应 dict；本日按官方 `steps/content` 结构处理，列表内是字典，text 片段的 text 是字符串。不扩展任意损坏的内层字段或旧 `outputs` 协议。
- 输出：最后一个 model_output 中全部 text 片段拼接成的 `str`，保留原文与首尾空白，不改变响应对象。
- 处理顺序：先检查供应商 status；然后从末尾寻找 model_output；找到后读取它的 content，选择文字片段并按原顺序拼接；最后验证拼接结果不是空白。
- `data.get("status") != "completed"`：抛 `ValueError("model_not_completed")`，即使存在部分文字也不返回。
- completed 但没有 model_output，或最后的 model_output 没有非空白文字：抛 `ValueError("missing_model_text")`。
- 缺少 steps/content 按空列表处理。最后一个 model_output 为空时不能回退到更早的答案；不能用 `pop()` 或 `reverse()` 改原数据。
- 不重试、不调用 HTTP、不检查引用、不改写答案；这几件事各有已有调用位置。

完成标准：上面的网关测试 **18 passed**；全日此时 **92 passed / 1 failed**（若独立测试未写）。目标包含 2026-10-12 补强的原有 type 筛选要求；当前学习者独立测试已经写完，不要求删除或还原。失败断言定位的是行为差异，不会自动诊断根因。

## 7. TODO 3：独立验证成功后无资料不会再次 POST（约 15～20 分钟）

只替换 `tests/test_day34_extra.py` 的占位函数，并自行补导入。复用已有 `answer_question()` 和 `review_qa_result()`，不写第二套问答算法。

给定条件与调用顺序：

1. 构造 `chunk = Chunk("faq.txt", 0, 0, 8, "返品期限は30日")`。
2. 在这个测试函数内部先创建 `http_calls = []`，它是本次测试自己的 HTTP 请求记录列表；再在同一个测试函数内部定义 `handler(http_request)`。`http_request` 是 MockTransport 在拦截 `client.post()` 时自动传入的 HTTP 请求对象。handler 执行 `http_calls.append(http_request)`，把它收到的这个对象放进外层测试的同一个列表；不用手动创建或传入请求。每次返回 HTTP 200，JSON 为：

   ```json
   {"status":"completed","steps":[{"type":"model_output","content":[{"type":"text","text":"返品期限は30日です。[1]"}]}]}
   ```
3. 创建**一个** `GeminiGateway("test-model", api_key="fake-test-key", transport=httpx.MockTransport(handler))`；两次调用使用这个同一对象。

   这里传入 `handler` 函数本身。调用顺序是 `answer_question → gateway.complete → client.post → MockTransport 调用 handler(http_request)`；HTTP 请求来自 `gemini_gateway.py` 的 `self.client.post(ENDPOINT, json=payload)`。handler 不是内部的 ModelRequest，也不是模型响应，而是负责接收请求、记录它并提供假响应的函数。
4. 先以 `[chunk]`、问题 `"返品"`、top_k=2、预算 100 调用 `answer_question()`。
5. 再以 `[chunk]`、问题 `"駐車場"`、同样上限和网关调用。使用 `try/finally`，最后 `gateway.close()`。

必须断言：

- 第一次 status 是 generated，answer **完整等于**固定日文回答，`review_qa_result()` 为 `[]`。
- 第二次 status 是 no_context，answer 完整等于 `NO_CONTEXT_ANSWER`，context.text 为 `""`、context.chunks 为 `[]`，编号检查返回 `[]`。
- 两次之后 `len(http_calls) == gateway.request_count == 1`，第二次没有清除第一条记录或增加 POST。
- 第一次实际 HTTP 请求解码后的**完整字典**为 model=`test-model`、system_instruction=`QA_INSTRUCTIONS`、input=`json.dumps({"question":"返品", "context":"[1] faq.txt (0:8)\n返品期限は30日"}, ensure_ascii=False)`、store=`False`。比较使用上述实际值，而不是调用 TODO 1 生成期望答案。
- `finally` 结束后 `gateway.client.is_closed` 为 True。

目的：原“无资料零调用”行为在换成 HTTP 适配器后仍成立。测试合法路径不抛异常；pytest 断言失败退出 1，全通过退出 0。只有删除占位、不写断言不能算完成。

## 8. 离线通过后再进行真实问答

仓库根目录先运行：

```text
.\.venv\Scripts\python.exe -m pytest Week5/day34/tests -q
.\.venv\Scripts\python.exe -m Week5.day34.code.run_live_qa --help
.\.venv\Scripts\python.exe -m Week5.day34.code.run_live_qa --live --case C
```

目标 **93 passed**；help 退出 0。C 无需密钥、不创建真实网关、不联网，输出 no_context、固定提示、空资料、gateway_calls=0；这是应用行为，不是模型拒答证据。

此前项目已使用 Gemini。真实入口沿用当前终端的 `GOOGLE_API_KEY` 或 `GEMINI_API_KEY`，默认 `gemini-3.8-flash`（本次官方文档核对支持）；可用 `--model` 显式选择账号可用模型。不要把密钥写进代码、聊天或笔记。存在性检查只打印布尔值：

```text
.\.venv\Scripts\python.exe -c "import os; print('API_KEY_PRESENT=' + str(any((os.getenv(name) or '').strip() for name in ['GOOGLE_API_KEY','GEMINI_API_KEY'])))"
```

用户级环境变量只会在新终端启动时继承；没有值时先打开已配置的新终端，不重新安装依赖。确认自己的账号及费用边界后，先 A、再 B，各发一次，不自动批跑或重试：

```text
.\.venv\Scripts\python.exe -m Week5.day34.code.run_live_qa --live --case A
.\.venv\Scripts\python.exe -m Week5.day34.code.run_live_qa --live --case B
```

每条只发送一个案例，30 秒 HTTP 超时，无自动重试；真实是否免费取决于账号，本材料不作费用承诺。输出一行 JSON，包括模式、模型、原 answer、context、citation_errors 和尝试调用数，不生成文件。

| 结果 | 退出码与表现 |
|---|---|
| 预览 / help / 正常返回 / C 无资料 | 0；回答质量另查 |
| 缺密钥 / 空模型名 | 2；missing_api_key / invalid_model |
| TODO 未实现 | 1；unfinished_todo |
| 4xx/5xx | 1；http_error 与 HTTP 状态码，不输出响应正文 |
| 连接 / 超时失败 | 1；network_error，无自动重试 |
| JSON 非法或不是对象 | 1；invalid_model_response |
| 任务未完成 / 无回答文字 | 1；model_not_completed / missing_model_text |
| 无效命令参数 | argparse 退出 2 |

不要将 200、退出 0、generated 或空 citation_errors 当成事实正确。若遇 403/429/超时，记录错误码，先检查权限/配额/连接；不靠连续重复请求修复。真正异常发生在网络或响应时，与尚未实现 TODO 的失败分别记录。

## 9. 人工核查与今日完成标准

在 [学习记录](./day34_notes.md) 按 A/B 分别保存可公开的原回答、实际发送来源与原文、编号错误列表、人工结论及理由。引用只核对**这次 context.chunks**，不找其他未发送文件来替模型证明。

- A：回答的 30 日是否确实在原文？引用是否对应实际资料？有无额外编造条件？
- B：原文没写送料承担方，模型是否拒答？若编造“顾客承担”，记录无依据；若无编号拒答，解释 missing_citation 不直接代表拒答内容错误。

模型答错也可以成为本日真实核查成果，保留失败证据，不要求反复调用直到满意。代码须通过 93 项、入口与错误检查；A/B 真实调用及人工核查、学习后复盘与自报用时均完成后才能结束本日。若账号/网络阻塞，明确记录真实核查待完成，不能拿离线测试代替。

无需重跑所有历史日；不新增 Prompt 改进作业，不补交旧题。完成后按项目规则验收与上传，当前材料建立不算学习完成。

## 10. 助手建立验证（非学习者必做）

- 复制 Day33 所需实现和测试，增加 TODO 前 **69 passed**；随后初始本日 **75 passed / 17 项预期失败**，全部失败对应三个 TODO，无警告。
- 根 Python **3.11.15**，httpx/既有依赖可用，pip check 通过；没有新增依赖或读取未经授权的终端日志。
- 官方请求字段、steps/model_output/content/text、completed 和当前模型名已用 Chrome 核对；本轮没有真实模型调用。后续临时参考验证与入口检查证据见当天笔记，不计学习者完成。

## 11. 历史检查（2026-10-12，当时尚未完成）

本节中的代码错误已修正，真实记录也已从授权日志补齐；这些待修正、待填写描述是当时状态，最终结论见下一节。

最新代码复查：学习者已将类型判断放在逐片段循环内，检查单个 content 字典，初始化和最终检查/返回的缩进正确；**93 passed，无警告**，pip check 通过。代码部分符合原要求，真实 A/B 记录仍空白，待核查原输出与人工结论；没有自动调用模型或上传。以下失败结果均为已解决的历史检查记录。

最新复查：学习者补了类型判断，但调用 contents.get，contents 实际是列表；当前 **87 passed / 6 failed**，六个失败同源。类型判断应放入 for content in contents 内并检查单个 content 字典，初始化与最后空白检查/返回仍在循环外。复盘状态与异常位置已改对，真实 A/B 记录仍空白，待核查实际结果；没有代改核心实现或自动调用模型。以下为此前检查记录。

- 学习者独立测试符合原要求：同一网关、两次不同问题、完整结果/请求字典、一次 HTTP、关闭连接均已断言。现有 92 项全部通过；手动检查发现 extract_answer 只判断有没有 text 值，没有判断片段 type。原 TODO 明确只拼接 type=text；原测试未覆盖非 text 片段同时带 text 字段的情况，这是助手覆盖遗漏。
- 补强一项原契约测试后为 **92 passed / 1 failed**，目标 **93 passed**。只需在拼接前筛选片段类型；核心实现仍由学习者修正。函数末尾旧 TODO 位于必抛异常后，已不可达，应清理；不把它当成这次失败根因。
- pip check、实际子进程 help/A/B/C 预览/C 零调用/缺密钥/非法参数退出码、UTF-8 JSON、无 traceback 和无输出文件通过。子进程隔离密钥环境，没有真实模型请求、未读取未经授权的 Cmder 日志，没有全仓回归要求。
- 复盘第 1 题正确，第 2 题需区分供应商 completed 与本地 generated、补 POST 总数 1，以及 HTTP 429 在 raise_for_status 抛出的位置；第 3 题需把“原文有问题”补准为原文是否包含送料答案。原答与助手说明分别保留在笔记。
- 学习者确认真实 A/B 尚未运行；自报用时 2h+、难度难，编号仍抽象。当前保持学习中，不提交推送；先修小范围代码，再回看本次实际发送的 [1] 与回答编号，不增加抽象编号概念或新功能。

## 12. 最终验收（2026-10-12）

- 两个核心函数与独立测试符合原契约；片段筛选、只取最后输出、原数据与原空白保留、同一网关先成功后无资料零新增 POST、完整请求字典和连接关闭均通过。最终 **93 passed，无警告**，pip check 通过。原覆盖遗漏已补测试，学习者完成核心修正；助手只补中文注释、整理测试字典排版和删除未使用导入。
- 授权读取的 Day34 Cmder 日志确认真实 A/B 各有完整结果及后续退出 0。A 为“返品期限は30日です。[1]”，原文明确写 30 日，有据；B 为“資料からは回答できません。”，原文未写送料承担方，拒答合理，仍有 missing_citation。C 为 no_context、零模型调用。完整原答案、来源和助手人工判断见当天笔记；没有重复真实模型调用。
- 日志有 11 轮完整 pytest 摘要，最后 93 passed；助手的历史检查结果另行记录，不混为学习者命令。既有实际入口 help、预览、C、缺密钥与参数错误、退出码、UTF-8、无 traceback/输出文件验证通过。学习用时仅采用自报 2h+，不以跨日日志时段推算。
- 本日收尾，概念仍需巩固。复盘原答保留，状态与异常位置的订正、调用数和编号/内容范围的助手补准分开记录；不要求重抄旧题。下一日先用本次实际 [1] 资料和 A/B 回答做一个具体对照，再沿问答核查主线缩小范围继续，不加惩罚性补课。按项目默认规则检查后提交上传，结果以远端核对为准。
