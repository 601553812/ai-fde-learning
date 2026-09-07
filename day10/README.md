# Day 10 — API 错误处理：严格模式与长度边界

日期：2026-09-07（日本时间）

状态：已完成（2026-09-08 最终验收）。参考用时：90～120 分钟；学习者自报实际用时 1.5 小时，反馈量合适。

本次实测：Day 10 `17 passed`，Day 6～10 `47 passed`，全仓 `88 passed`；正常、400/413/422、长度边界、日文输出、无输出文件和错误后的再次成功请求均验证通过。核心代码不需返工。复盘解释、学习者订正与最终澄清见 `day10_notes.md`；最后一次回答已由学习者澄清为看成 strict=true，完成复盘确认。原始 TODO 和初始失败说明保留用于回顾，不代表当前仍未完成。

## 今天解决什么问题

Day 9 能返回需求分析结果，但调用者有两种用途：

- 草稿检查：即使需求不完整，也要看到分析结果和缺项列表。保留默认 HTTP 200。
- 严格检查：不完整就拒绝本次操作，调用者根据非成功状态走错误处理。增加 `strict=true`，缺项时 HTTP 400。

今天唯一主主题是“明确的 API 错误契约”。按你的反馈增加一项独立功能：文本超过 2000 个字符时拒绝处理，练习边界值和错误优先级。不是另加一个框架。

继续使用 Day 6 的 parser、业务校验、输出模型以及 Day 9 的请求模型，不修改历史学习日。Day 10 的新应用是独立的 FastAPI 实例，不直接给 Day 9 的 app 添加路由。2000 字符以内的默认分析行为保持不变；超长拒绝是明确新增的限制。

## 先看非测试代码

先打开 `app.py`，从 `analyze_requirement()` 看输入到输出，不急着改两个辅助函数。

```text
POST /analyze-requirement?strict=true + JSON body
  → FastAPI 解码 JSON、校验 body 和 query（不合法：422，路由不执行）
  → request 已是 AnalyzeRequest；strict 已是 bool
  → check_text_length(text)                 ← TODO 1，过长：413
  → parse_requirement(text)                ← 复用
  → validate_result(requirements)          ← 复用，返回全部业务缺项
  → check_business_errors(errors, strict)  ← TODO 2，严格模式且有缺项：400
  → build_output(requirements, errors)     ← 复用
  → AnalysisOutput → HTTP 200 JSON
```

复习：Requests/TestClient 是调用侧，FastAPI 是接收侧。TestClient 仍返回 Response，先检查 `status_code`，再用 `.json()` 读响应。今天除一个已提供的“禁止调用 parser”测试外，直接测试本地真实调用链，不需要 FakeResponse。

## 最小知识集

### 1. query 与 body 是两个输入位置

本题路由签名已给出：

```python
def analyze_requirement(request: AnalyzeRequest, strict: bool = False) -> AnalysisOutput:
    ...
```

`request` 的模型来自 JSON body；`strict` 是不在路径中的简单类型参数，来自 URL 的 `?strict=true`。省略它时取默认值 False。可以类比 Java Web 的请求 DTO 与 `@RequestParam`，但这里由 FastAPI 读取类型和默认值决定绑定，不是 Java 注解机制。

最小调用方式：

```python
response = client.post(
    "/analyze-requirement",
    params={"strict": "true"},      # URL query
    json={"text": "機能: 登録"},   # JSON body
)
```

URL 的 `"true"`/`"false"` 会被转换为 Python bool；不要自己写 `bool("false")`，非空字符串这样计算也是 True。`"banana"` 不能解析为 bool，本环境会返回 422。`strict` 是本题业务模式名称，不是 Pydantic 的严格类型模式。

把 strict 放进 body 会违反已有 `extra="forbid"` 规则，返回 422。请求 body 的 `text` 字段仍保持必填、字符串、非空，不新增字段。

来源：[FastAPI 查询参数：默认值与类型转换](https://fastapi.tiangolo.com/tutorial/query-params/)。今天只需要本节用法，不需要阅读其他参数 API。

### 2. 用 raise HTTPException 明确中断本次请求

一个与练习不同的小例子：

```python
from fastapi import HTTPException

def require_available(available: bool) -> None:
    if not available:
        raise HTTPException(status_code=409, detail={"code": "RESOURCE_BUSY"})
```

输入 False 时抛异常；输入 True 时正常结束，隐式返回 None。可以把 `-> None` 对照 Java 的 void 理解“没有业务返回值”，但 Python 仍实际返回 None，也不是强制检查的返回类型。

`raise` 类似 Java 的 `throw`：即使发生在路由调用的辅助函数里，也会中断剩余调用链。FastAPI 的异常处理机制把它转换为指定状态码和 `{"detail": ...}` 的 JSON 响应。结束的是本次处理，不是整个服务器。

参数只用两个：`status_code` 是 HTTP 状态码；`detail` 是错误内容，可以是字符串或可 JSON 序列化的 dict/list。这里选 dict，让调用者使用稳定的 `code` 判断错误。

不能写 `return HTTPException(...)`。本题辅助函数的返回值不会被路由使用，返回一个异常对象不会中断流程。只 `return {"detail": ...}` 也不会自动把 HTTP 状态改成 400；在声明成功响应模型的路由里，还可能导致响应校验错误。

来源：[FastAPI 错误处理：HTTPException](https://fastapi.tiangolo.com/tutorial/handling-errors/)。今天不看该文后面的自定义全局 handler。

### 3. 三种失败位置，不要都当成 500

| 输入与模式 | 状态 | 谁负责 | 响应重点 |
|---|---|---|---|
| 合法且完整；默认或 strict=true | 200 | 原解析和输出逻辑 | AnalysisOutput |
| 合法但业务缺项；默认或 strict=false | 200 | 原业务校验 | validation_errors 列出缺项 |
| 合法但业务缺项；strict=true | 400 | 你写的业务错误策略 | detail.code 与 detail.errors |
| 合法请求，text 长度大于 2000；任意模式 | 413 | 你写的长度策略 | detail.code 与长度信息 |
| 损坏 JSON、缺少/空/错误类型的 text、额外 body 字段、错误 strict 值 | 422 | FastAPI/Pydantic | detail 错误列表 |

400 是本练习对“严格检查不接受不完整需求”的契约选择，并非所有 API 必须这样设计。422 保留框架默认行为；不把 Day 9 的默认业务结果改成失败。

自定义错误的 detail 是 dict；框架 422 的 detail 是 list，两者不是同一结构。成功结果的 `requirements` 才包含 `functions` 等分类；错误响应不返回完整分析结果。

`responses={400: ..., 413: ...}` 已在装饰器里提供，用来给 `/docs` 添加错误描述，不会替你实现检查。HTTPException 的错误响应由异常处理机制产生，不要求满足成功用的 AnalysisOutput 模型。

## 五个 TODO

只需要修改 `day10/app.py`、`day10/test_day10.py` 和学习记录。保留路由已提供的调用顺序、模型和原解析规则。

### TODO 1：长度限制 — app.py 的 check_text_length

- 输入：已通过请求模型校验的 text 字符串；上限常量 `MAX_TEXT_LENGTH = 2000` 已提供。
- 处理：用 `len(text)` 计算原始字符串长度，包含换行、空格和注释，不先 strip；长度 **大于** 上限才拒绝，恰好等于允许。
- 正常输出：None，不抛异常；函数可以正常走到结尾。
- 异常：抛出 HTTPException，状态码 413，detail 为以下 dict；长度值必须根据本次输入计算，不写死。

```json
{"code": "TEXT_TOO_LONG", "max_length": 2000, "actual_length": 2001}
```

- 完成条件：2000 个字符的日文输入通过；2001 个字符被拒绝；超长时还没有调用 parser。已提供测试验证边界、顺序和完整错误 body。
- 错误响应只含长度信息，不回显原文。这里的“字符”按 Python Unicode 码点计数，不是 UTF-8 字节数，也不保证等于视觉字符数。
- 范围限制：检查发生在 body 已读入和模型已构造之后，**不是**生产级 HTTP body 大小限制或抗超大请求方案。今天不处理代理/服务器层限制。

### TODO 2：严格模式 — app.py 的 check_business_errors

- 输入：`validate_result()` 给出的 `list[str]` 和已转换的 bool strict；不要重新解析文本或再构造一套业务规则。
- 处理：只在 strict 为 True **且**错误列表非空时拒绝。其他组合正常结束；`[]` 可用于假值判断。
- 正常输出：None，不修改输入错误列表。
- 异常：HTTP 400，detail 的 code 为 `REQUIREMENT_INCOMPLETE`，errors 必须保留传入列表的全部内容与顺序。例如两个缺项时：

```json
{
  "detail": {
    "code": "REQUIREMENT_INCOMPLETE",
    "errors": [
      "At least one function is required",
      "At least one acceptance criterion is required"
    ]
  }
}
```

上面是完整 HTTP body；传给 HTTPException 的 detail 只是内层 dict，不要再套一层 detail。

- 完成条件：默认/显式 false 保留 200；strict=true 且完整仍为 200；strict=true 且缺项返回 400/完整错误列表。不要 `except Exception` 把它吞掉或改成 500。

### TODO 3：单缺项测试 — test_strict_only_missing_acceptance

替换函数中的 `pytest.fail()`，按 Arrange–Act–Assert 写真实断言。

- 输入：`"機能: CSV出力"`，query strict=true。
- 输出：HTTP 400；完整 body 为 `{"detail": {"code": "REQUIREMENT_INCOMPLETE", "errors": ["At least one acceptance criterion is required"]}}`。
- 完成条件：同时断言状态码和整个错误 body；不能出现缺少功能的错误。它用于防止 TODO 2 写死“双缺项”样例。

### TODO 4：空白输入测试 — test_whitespace_depends_on_strict_mode

替换 `pytest.fail()`，对相同输入 `"   \n  "` 分别请求 strict=false 和 strict=true。

- false：200，requirements 的五个分类都为 `[]`，validation_errors 为已有常量 `MISSING_BOTH`。
- true：400，完整 body 为 detail.code `REQUIREMENT_INCOMPLETE` 和 detail.errors `MISSING_BOTH`。
- 完成条件：两个状态和上述结构都断言。不要把输入改成空字符串：`""` 在请求模型阶段就是 422，测不到业务校验。

### TODO 5：错误后的下一次请求 — test_valid_request_after_business_error

替换 `pytest.fail()`，在同一个测试里使用已有 client 顺序请求：

1. strict=true，输入 `"機能: 登録"`，断言 400 与仅缺验收条件的错误。
2. strict=true，输入 `"機能: ログイン\n受入条件: 1秒以内"`，断言 200、版本字符串 `"1.0"`、functions 为 `["ログイン"]`、acceptance_criteria 为 `["1秒以内"]`、validation_errors 为 `[]`。

完成条件：两次请求都必须执行并有上述断言；不能用测试替身直接返回期望响应。此测试观察处理错误后应用仍可正确响应，且前一次错误没有混入新结果；不宣称它覆盖了所有并发/生命周期问题。

## 先读测试时注意

- `test_over_limit_precedes_business_check` 已提供 monkeypatch：替换的是路由模块使用的 `day10.app.parse_requirement`，一旦它被调用测试就失败。这是验证“必须先拒绝再解析”，不是模拟 HTTP 返回结果。
- `test_requests_do_not_create_output_files` 已提供临时目录，并在每次请求后断言目录仍空，真实检查不生成输出文件。接口也不应调用外部网络。
- 不修改已有断言来绕开 TODO，不用 skip/xfail；保留三项测试函数，用自己的实现替换其中的 pytest.fail。

## 学习顺序与运行

- 0～10 分钟：填开始时间，读 Day 9 复盘订正，再看本日调用链。
- 10～30 分钟：读最小知识集，分清 params/json、raise/return。
- 30～60 分钟：完成两个错误策略，逐项运行已有测试定位错误。
- 60～90 分钟：写三项测试，重点检查 JSON 层级、类型和边界值。
- 90～110 分钟：真实 HTTP 验证；最后复盘与自报用时，结束时间在笔记最后一行填写。

根目录 `.venv` 继续使用，不新增依赖。以下一行命令 PowerShell 与 CMD/Cmder 通用，均在仓库根目录执行：

```text
.\.venv\Scripts\python.exe -m pytest day10/test_day10.py -q --tb=short
.\.venv\Scripts\python.exe -m pytest Week1/day06/test_day06.py Week1/day07/test_day07.py day08/test_day08.py day09/test_day09.py day10/test_day10.py -q --tb=short
```

初始预期：Day 10 `11 passed, 6 failed`；两个辅助函数暂时是 pass，保留旧行为但不执行新增限制，导致三项已提供测试失败；另三项是自写测试 TODO 的主动失败。这不是安装故障。完成两个策略后应为 `14 passed, 3 failed`；完成全部任务目标为 `17 passed`，Day 6～10 合计 `47 passed`。

脚手架实测（2026-09-07）：上述 `11 passed, 6 failed` 已确认，Day 6～10 为 `41 passed, 6 failed`；历史 Day 1～9 的现有测试仍为 `71 passed`，`pip check` 通过。真实 Uvicorn 的健康检查、docs HTML、OpenAPI 中的 strict query/default、日文正常响应和 422 可用；严格缺项与超长请求暂时仍是 200，符合 TODO 未实现状态。临时验证目录无输出文件，临时服务已停止。

沿用环境中的两条间接依赖弃用警告，不影响练习，也不需要屏蔽。如果实现里出现未捕获的普通异常，TestClient 默认会把它抛到测试中；正确抛出的 HTTPException 则会变成可断言的 HTTP 错误响应。

## 真实 HTTP 验证

终端 A 启动 **day10** 应用，用 8010 端口与旧服务区分（两种 shell 通用）：

```text
.\.venv\Scripts\python.exe -m uvicorn day10.app:app --host 127.0.0.1 --port 8010 --reload
```

终端 B（PowerShell / CMD / Cmder 通用；使用 curl.exe）：

```text
curl.exe -i http://127.0.0.1:8010/health
curl.exe -i -H "Content-Type: application/json" --data-binary "@day10/incomplete_request.json" http://127.0.0.1:8010/analyze-requirement
curl.exe -i -H "Content-Type: application/json" --data-binary "@day10/incomplete_request.json" "http://127.0.0.1:8010/analyze-requirement?strict=true"
curl.exe -i -H "Content-Type: application/json" --data-binary "@day09/sample_request.json" "http://127.0.0.1:8010/analyze-requirement?strict=true"
curl.exe -i -H "Content-Type: application/json" --data-binary "@day09/invalid_request.json" http://127.0.0.1:8010/analyze-requirement
```

实现后依次预期：200/ok、200/含缺项、400/单缺项、200/完整日文分析、422/字段类型错误。第三次错误后第四次仍成功。再次提醒：curl 默认收到 HTTP 400/422 时仍可能正常退出，进程退出码不等于 HTTP 状态码。

超长用例不用生成大文件，终端 B 执行（两种 shell 通用）：

```text
.\.venv\Scripts\python.exe -c "import requests; s=requests.Session(); s.trust_env=False; r=s.post('http://127.0.0.1:8010/analyze-requirement', params={'strict':'true'}, json={'text':'x'*2001}, timeout=5); print(r.status_code); print(r.json())"
```

预期 413 与长度 2001 的错误，不是 400。这个命令中的 Requests 是外部调用者；服务端并没有向外发送请求。

打开 [本地接口文档](http://127.0.0.1:8010/docs)，确认 title 是 Day 10、strict 位于 query、body 仍是 text，再执行正常/严格失败各一次。观察终端 A 的状态码，无预期错误的 traceback；完成后 Ctrl+C 停止自己启动的服务。

脚手架阶段，400/413 请求暂时仍返回 200；要完成 TODO 才会符合新增契约。`/docs` 中列出状态码不代表该行为已实现。

## 今天不需要学习

全局异常处理器、改写 422 格式、统一全部错误 Schema、中间件、异步、依赖注入、数据库、LLM、重试、认证、Docker、框架继承源码以及生产级请求体限流。本日只用同步函数和默认异常处理机制。

## 完成标准

- 17 项本日测试和 47 项 Day 6～10 回归通过；三项自写测试包含各自要求的实际断言。
- 默认分析、分类、日文输出和请求模型规则保持；新增 400/413 的状态、结构、边界与执行顺序准确。
- 正常和失败请求不产生输出文件，不调用外部 API；自定义 400/413 不回显输入原文，不输出 traceback。
- 注意框架默认 422 可能带有错误字段输入，今天没有实现通用脱敏机制；只使用本项目自制样例，不拿真实敏感数据测试。
- 完成真实 HTTP 验证和学习复盘，能自行说明输入来源、raise 的作用和三阶段校验；时长自己填写，结束时间最后填写。
- 告诉我 `Day 10 完成，请检查`；验收通过、复盘和进度更新后，再按项目规则自动提交并推送 GitHub。当前脚手架不是已完成学习成果。
