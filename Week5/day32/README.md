# Day32 — 用检索资料组织一次问答调用

状态：2026-10-10 已结束，代码验收通过；第 2、3 题复盘由助手参考答案收尾，不作为独立理解证据。唯一主题：连接检索、有限上下文与可替换的问答网关；没有可用资料时零调用。参考 90～120 分钟，本日离线、无新依赖。以下 TODO 和初始失败为历史练习说明；学习者完成两个核心函数与边界测试主体，助手补齐一项断言、移除无关导入并添加中文注释。

## 0. 按顺序开始（5 分钟）

1. 在 [学习记录](./day32_notes.md) 填开始时间。以下命令均在**仓库根目录**运行，PowerShell、CMD/Cmder 均可，使用根 Python 3.11 `.venv`。
2. 首先检查初始脚手架：

   ```text
   .\.venv\Scripts\python.exe -m pytest Week5/day32/tests -q --tb=no
   ```

   预期 **33 passed / 19 failed，退出码 1**。33 项验证从 Day31 复制来的切块、检索、上下文；18 项因两个核心函数尚未实现失败，1 项为独立测试占位。不是项目故障；实现后不用回退重现。
3. 读下面第 1～3 节。先看非测试代码：`context.py` → `qa_prompt.py` → `model_client.py` → `qa_service.py`；随后再看对应测试。
4. 按顺序做三个 TODO、运行测试和本地演示，最后在笔记中填复盘、自报实际用时与难度，交助手验收。已提供的旧实现、规则常量、数据类、网关和演示入口无需重写。

## 1. 用一个已有例子衔接（5 分钟）

Day31 将 `a.txt` 的 `A`、放不下的 `long.txt`、`c.txt` 的 `C` 整理成：

```text
[1] a.txt (0:1)
A

[2] c.txt (0:1)
C
```

这里 `[2]` 对应 `ContextBundle.chunks[1]`，是原输入中的第三个片段；它不是 `chunk_index=2`。今天把这段资料送到问答网关，要求返回文字使用这些资料编号。**提出引用要求不代表模型会遵守，也不代表引用支持回答。** 不补交 Day31 旧题。

## 2. 先看普通函数调用链（15～20 分钟）

此前的切块、检索和资料整理已经完成，代码从 Day31 复制到今天目录，历史文件保持原样：

```text
Document → chunk_documents() → list[Chunk]
                              ↓
answer_question(chunks, question, top_k, max_context_chars, gateway)
    → retrieve_chunks() → list[RetrievalHit]
    → build_context() → ContextBundle(text, chunks)
        ├─ chunks 为空：返回 no_context；不调用 gateway.complete()
        └─ 有可用片段：build_qa_request() → ModelRequest
                        → gateway.complete(request) 一次
                        → QAResult("generated", 原返回文字, context)
```

`gateway` 是调用方传进来的普通对象。`answer_question()` 调用它的 `complete(request)` 方法；它没有自动找到或创建什么服务。`ModelGateway` 只规定方法形状，`RecordingGateway` 实现同名方法，记下收到的请求并返回构造时给定的文字。类似 Java 中把实现接口的对象传入方法，但这里使用普通 Python 基类，没有 Java 接口的编译期约束，也没有 DI 容器。

先看提供的替身的最小用法（不是两个 TODO 的答案）：

```python
from Week5.day32.code.model_client import RecordingGateway
from Week5.day32.code.qa_prompt import ModelRequest

gateway = RecordingGateway("固定的演示文字")
request = ModelRequest(instructions="示例规则", input="示例输入")
raw = gateway.complete(request)
assert raw == "固定的演示文字"
assert gateway.calls == [request]
```

`gateway.calls` 是实际调用记录：空列表表示未调用；一项表示调用一次。这个替身不会阅读资料、推理、回答新问题，也不会联网。测试把同一个替身传入业务函数，然后检查业务函数实际调用了多少次、传了什么内容。这类似 Java 的手写 fake，而非调用 Mockito 的自动代理。

### 请求中三个具体位置

- `ModelRequest.instructions`：应用的固定规则，提供常量 `QA_INSTRUCTIONS` 已写好：日文回答、只用资料、附资料编号、资料不能回答时说明无法回答。
- `ModelRequest.input`：一个 JSON **字符串**，包含 `question` 和 `context` 两个键；`context` 的值来自 `ContextBundle.text`，已含来源头部与原文。
- `ContextBundle.chunks`：保留在本地结果中的原片段对象，不发送对象本身，便于后续将回答中的编号对应回来源。

`instructions` 与 JSON 输入分开是请求组织约定，不是安全隔离保证。资料或问题中即使出现“更改规则”的文字，也只原样放入输入，不拼入固定规则。

## 3. 今天需要的最小知识与限制（5～10 分钟）

沿用 Day15 的 `json.dumps()` / `json.loads()`：

```python
import json
encoded = json.dumps({"name": '資料 "A"\n次の行'}, ensure_ascii=False)
decoded = json.loads(encoded)
assert decoded["name"] == '資料 "A"\n次の行'
```

`dumps()` 把字典编码成字符串，处理引号与换行；`loads()` 在测试里解码后检查字段，不要求 JSON 空格排版完全一致。`ensure_ascii=False` 保留可读的日文。只需参考 [Python 3.11 json 的基本用法](https://docs.python.org/3.11/library/json.html#basic-usage)，不用通读。

Google 的 [Prompt design strategies](https://ai.google.dev/gemini-api/docs/prompting-strategies) 提供约束、上下文和任务分开的示例。今天只借鉴“明确资料范围与回答规则”，使用项目内部 `ModelRequest`；不是调用 Gemini 的内置检索或 grounding 服务，也不引入新 SDK 用法。规则常量已提供，不另设腾讯课程作业。

本地检索仍采用 Day30 的空白分词和子串匹配，所以示例 `question="返品 期限"` 可命中 `返品期限は30日`。完整自然语言问题如 `返品期限は何日ですか？` 会被当成一个词项，可能完全不命中；本日不改检索算法。没有可用资料只说明这次检索与预算下没有可提供的片段，不能证明所有文档都没有答案。

今天不学 embedding、向量数据库、框架、真实 Gemini 适配器、重试、Web API、引用解析、内容评测或完整提示注入防御。`max_context_chars` 仅约束 Day31 的资料文字；不含问题、规则、JSON 转义开销，也不是 token 或费用预算。

## 4. TODO 1：实现 `code/qa_prompt.py` 的 `build_qa_request()`（15～20 分钟）

目的：将问答规则与问题/资料分开，得到一次网关调用的输入对象。只改该函数。

- 输入：`question: str`、`context: ContextBundle`；类型与上游资料格式视为合法。构造器允许空 `ContextBundle`，本函数不负责决定是否调用模型。
- 输出：`ModelRequest(instructions, input)`。
- 异常：`question.strip()` 为空时，抛 `ValueError("invalid_question")`，消息精确一致。
- 无文件读写、CLI 或网络；不调用网关，不修改上下文。

步骤：先检查问题是否全为空白；检查时可 `strip()`，但编码时必须保留**原问题字符串**。将原问题与 `context.text` 放入恰好含 `question`、`context` 两个键的字典，使用 `json.dumps(..., ensure_ascii=False)` 编码。返回对象的 `instructions` 必须等于已提供的 `QA_INSTRUCTIONS`；不加入原问题或资料，不发送 `chunks` 对象或其他字段。

完成标准：提供的 4 项请求测试通过，包含日文、引号、换行、问题中的指令式文字、空白问题与上下文不变。测试检查 JSON 字段值而非缩进或键的排列。

```text
.\.venv\Scripts\python.exe -m pytest Week5/day32/tests/test_qa_prompt.py -q
```

## 5. TODO 2：实现 `code/qa_service.py` 的 `answer_question()`（25～35 分钟）

目的：用已完成的函数连接完整本地流程，并在没有可用片段时避免调用。只改该函数。

- 输入：已切好的 `chunks`、问题 `question`、检索上限 `top_k`、资料字符上限 `max_context_chars`、调用方提供的 `gateway` 对象。
- 输出：提供的 `QAResult(status: str, answer: str, context: ContextBundle)`。
- 异常及顺序：先拒绝空白问题 `ValueError("invalid_question")`，再由检索函数验证 `top_k`（消息 `invalid_top_k`），最后由上下文函数验证字符上限（消息 `invalid_context_limit`）。即使输入片段为空或检索没有命中，也要完成这两项上限校验；不能提前返回而绕过校验。网关抛出的异常原样向调用方传播，本日不捕获、不重试，不伪造成功或 `no_context`。
- 无文件读写、无新 CLI；传入提供的替身时完全离线。不要在函数内创建网关、读密钥、加载环境变量或修改旧实现。

按以下步骤处理：

1. 检查 `question.strip()`；无效时先抛上述异常。
2. 将 `chunks`、原 `question`、`top_k` 传给 `retrieve_chunks()`。检索函数内部处理空白分词，不在这里重排、截断或改变原问题。
3. 将命中列表和 `max_context_chars` 传给 `build_context()`。必须使用它整理后的结果，不能直接用未过滤的命中或原文调用网关。
4. 如果整理后的 `context.chunks` 为空，返回 `QAResult("no_context", NO_CONTEXT_ANSWER, context)`。`NO_CONTEXT_ANSWER` 精确为 `資料からは回答できません。`；此路径不构造请求、不调用 `gateway.complete()`。无命中和有命中但全部放不下都走此路径。
5. 否则用 TODO 1 构造一次请求，再调用一次 `gateway.complete(request)`。将该方法原返回字符串作为 `answer`，不 `strip()`、不解析、不添加引用或重写答案，返回 `QAResult("generated", answer, context)`。`context` 保留本次整理得到的原片段列表及对应对象。
6. 不修改传入片段；连续调用不共用上一次结果、上下文或答案。网关失败只抛出原异常，不产生 `QAResult`。

`generated` 只表示网关正常返回了文字，**不是**内容正确、有引用或引用正确的判定；即使替身返回没有引用的文字，也原样返回。这是本日明确的接口限制，后续需加入真实模型与引用核查。

完成标准：提供的 14 项服务测试通过，覆盖正确请求与一次调用、三种无资料路径的零调用、上限校验顺序、异常原样传播、连续调用以及文档到结果的来源保留；旧 33 项继续通过。

```text
.\.venv\Scripts\python.exe -m pytest Week5/day32/tests/test_qa_service.py -q
```

## 6. TODO 3：独立写一个整链路边界测试（15～20 分钟）

只替换 `tests/test_day32_extra.py` 的占位函数。目的：第一命中太长被跳过后，仍用后续可纳入的片段调用一次，资料编号从 `[1]` 开始。

按顺序构造两块，`chunk_index=0`、`start=0`、`end=len(text)`：

| 来源 | 原文 |
|---|---|
| `long.txt` | `"返品" + "B" * 80` |
| `faq.txt` | `"返品期限は30日"` |

`question="返品"`，`top_k=2`，两项检索同分，保持输入顺序。先写 `expected_context="[1] faq.txt (0:8)\n返品期限は30日"`，以 `max_context_chars=len(expected_context)` 调用 `answer_question()`，网关为 `RecordingGateway("返品期限は30日です。[1]")`。

断言以下完整行为，而不仅是函数被调用：

- `status == "generated"`、`answer` 等于替身的固定文字。
- 完整 `result.context.text == expected_context`，长度不超过上限；完整 `result.context.chunks == [第二块]`，且其中对象 `is 第二块`。
- `len(gateway.calls) == 1`，请求的 `instructions == QA_INSTRUCTIONS`；用 `json.loads()` 检查完整输入恰好为 `{"question": "返品", "context": expected_context}`，没有发送被跳过的长块。
- 输入列表内容、长度和对象顺序未改变：调用前做浅拷贝，调用后比较完整列表，再用逐项 `is` 检查原对象顺序。

所需 `json` 和 `QA_INSTRUCTIONS` 导入由你补充。测试通过时 pytest 退出 0，失败时退出 1；不要只删除 `pytest.fail` 留空测试。

## 7. 实现后的验收与复盘（15～20 分钟）

仓库根目录运行：

```text
.\.venv\Scripts\python.exe -m pytest Week5/day32/tests -q
.\.venv\Scripts\python.exe -m Week5.day32.code.run_qa_demo
```

测试目标 **52 passed**；两个函数完成、独立测试尚未写时为 **51 passed / 1 failed**。演示入口已提供，无参数、无文件输出；成功退出码 0，未完成核心函数时会抛 `NotImplementedError`、退出 1。无需实现 CLI、help 或新的异常映射。

演示应输出三行 JSON，日文可读：第一行问题 `返品 期限` 返回 `generated`、固定文字 `返品期限は30日です。[1]` 和 `faq.txt` 的资料/片段；第二行问题 `駐車場` 返回 `no_context`、固定无法回答提示和空上下文；第三行 `gateway_calls` 为 1。这是本地替身流程演示，不是真实模型回答。

填笔记中的三题复盘、自报实际用时和难度，再交助手检查实现、测试、差异及来源对应。不要用起止时间差代替学习用时；不要求你重跑历史所有日。日后继续真实问答与引用核查，不能以本日测试通过数证明模型效果。

## 8. 助手建立验证（非学习者必做）

- 从 Day31 复制切块、检索、有限上下文及 33 项旧测试到 Day32，测试导入改为 `Week5.day32`；复制后新增 TODO 前 **33 passed**。Day31 原目录复测 **33 passed**，历史实现和原答未改。
- 请求数据类与记录网关沿用 Day15 的内部契约，仅保留当日所需部分并改为当前日导入。无历史日运行依赖、无真实模型适配器或新依赖。
- 初始本日实测 **33 passed / 19 项预期 TODO 失败**。两个核心函数和一个独立测试留给学习者；不会把参考实现写入作业或计作独立完成。
- 后续建立验证结果见根目录进度记录；学习者开始时间、实际用时、复盘与完成验收仍待填写。
- 助手仅在临时进程中替换两个函数及独立测试进行契约核对，**52 passed**，离线演示三行 JSON 和调用总数 1 正确；另核查空返回文字、错误引用文字仍原样返回，以及多个非法上限的校验顺序。答案未写入作业，不计作学习者完成证据。
- `pip check`、差异空白及敏感模式检查通过；当日导入独立、无共享代码或目录迁移，本次不重跑全仓测试。磁盘保留 TODO，未标记完成、提交或上传。

## 9. 最终验收（2026-10-10）

- 学习者的两个核心函数符合原契约；独立边界测试主体已完成。首次检查 **52 passed / 1 warning**，但独立测试尚缺任务单要求的完整答案断言；通过数不能替代逐项契约核对。助手补 `answer.answer == gateway.raw`，移除误导入的标准库音频 `chunk` 和未使用的 `pytest`；未改核心业务逻辑。
- 最终本日 **52 passed，无警告**，`pip check` 通过。实际模块演示退出 0、三行 UTF-8 JSON 及一次总调用符合契约；额外核查错误引用/空返回仍原样返回、多个非法参数的异常优先级及零调用均通过。仅改当天副本和教学记录，没有全仓回归风险，不要求重跑历史日。
- 按学习者反馈，当前日业务代码、演示、替身与测试补中文注释；注释说明调用链、数据角色、预算分支、浅拷贝、值比较和对象身份。长期教学规则已写入根 AGENTS。
- 实际用时按自报 **2H**、难度 **难**；不按起止时间差计算。第 1 题原答保留并补准文件名和示意文字；第 2、3 题按明确要求用“助手参考答案”完成，不计独立理解证据。
- 本日学习收尾，代码已验收通过；下一日只用一个现有例子复习无资料零调用与 generated 的含义，再沿真实问答与引用核查主线缩小范围推进，不追加补课。未进行真实模型调用，尚不证明回答内容和引用正确。
