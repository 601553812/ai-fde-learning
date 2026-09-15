# Day 11 — 可替换分析服务与依赖注入

日期：2026-09-08（日本时间）

状态：2026-09-09 已完成本日收尾；代码验收通过，概念理解待巩固。学习者自报 2h，反馈偏难并明确要求直接提供复盘参考答案、结束当天；参考答案见学习记录，不作为独立掌握的证明。

最终验收：Day 10～11 为 33 passed，全仓 104 passed，pip check 通过；真实 HTTP 正常/错误路径、固定 503、长度优先、日文 UTF-8、无输出文件和服务隔离检查通过。下文保留最初任务设计及脚手架失败记录，均不代表当前仍未实现。下次先复习一个已有调用案例，不继续加量。

## 今天解决什么问题

以后分析器可能从规则解析换成 LLM 调用。路由不应该为此重写所有 HTTP 逻辑；测试也不应该每次都付费调用真实服务。

今天唯一主主题是“把分析器作为可替换的依赖”。用 FastAPI 的 Depends 获得分析器，用 dependency_overrides 在测试中替换它。沿用 Day 10 的错误边界，再增加同主题的独立功能：**分析服务暂不可用时，返回安全的 HTTP 503**。

今天不接真实 LLM，不需要密钥或新增依赖。规则分析器只是把已经验证的三步解析逻辑包成一个对象方法，不重写旧 parser。本日的“服务”是程序内的 Python 对象，不代表又部署了一个服务器；后续它才可能封装外部调用。

## 先复习，再看非测试代码

- `response.json()["requirements"]` 是 dict，其中 functions 等字段的值是 list；可以类比 Java 的 `Map<String, List<String>>`。
- 对格式合法、未超长但缺业务项的文本：strict=False 返回 200，缺项在 validation_errors；strict=True 返回 400，缺项在 detail.errors。不要把模式与测试/生产环境对应。

阅读顺序：`service.py` → `app.py` → 已提供的一个替换测试；最后才写 TODO。

目标调用链（当前脚手架仍保留旧解析块，TODO 1 要把它替换掉）：

```text
FastAPI 获得请求数据，并解析 Depends(get_analyzer)
  → 调用 get_analyzer，取得 RuleBasedAnalyzer 对象
    （测试时可改为调用 override_analyzer，取得 fake 对象）
  → 路由：check_text_length(text)                超长 → 413
  → invoke_analyzer(analyzer, text)
      → analyzer.analyze(text)                  服务不可用 → 503
      → 得到 AnalysisOutput
  → check_business_errors(output.validation_errors, strict)
                                                 严格且有业务缺项 → 400
  → 返回 output，由框架生成 HTTP 200 JSON
```

body/query 校验失败仍为框架的 422。不要假定 provider 一定在 body 校验之后才运行；依赖解析发生在路由执行之前。本日保证的是 **超长时不调用 analyze()**，不是“完全不创建分析器对象”。因此 provider 应保持轻量，不在创建对象时执行外部请求。

## 最小知识集

### 1. provider、对象与方法，分别是什么

`service.py` 已提供：

- `get_analyzer`：一个函数，负责提供分析器。
- `get_analyzer()`：执行这个函数，得到 RuleBasedAnalyzer 实例。
- `analyzer.analyze(text)`：调用对象的方法，返回 AnalysisOutput 模型。
- `AnalyzerUnavailable`：表示已知临时不可用情况的异常类；它不是 HTTP 响应，不依赖 FastAPI。

默认 RuleBasedAnalyzer 的 analyze 只是原来的 `parse_requirement → validate_result → build_output`。长度限制和 strict 的 HTTP 策略仍放在路由侧。

Java 类比是“Controller 使用外部提供的 Service，而不是自己 new 后固定使用”；这个例子采用路由参数注入，并不等同于 Spring 的完整容器、生命周期或接口机制。Python 的类型标注也不等于 Java 的编译期类型检查。今天的测试替身继承 RuleBasedAnalyzer 并重写 analyze，暂不引入抽象基类或 Protocol。

### 2. Depends 让框架调用 provider

路由参数已提供：

```python
analyzer: RuleBasedAnalyzer = Depends(get_analyzer)
```

读法：“这个参数需要 RuleBasedAnalyzer；请 FastAPI 调用 get_analyzer，并把结果放到 analyzer 中。”

`Depends(get_analyzer)` 传的是函数本身；不要写 `Depends(get_analyzer())`，那会提前调用 provider，把返回对象当成依赖 callable，含义不同。也不要在路由中再次调用 get_analyzer 或 new 一个对象，否则会绕过已经注入的替身。

这不是普通 Python 自动执行依赖：直接手动调用路由函数时，默认参数仍是 Depends 标记，不会替你完成注入。所以接口测试用 TestClient 发起请求；单测真实分析器则可以直接调用其 analyze 方法。

今天选官方也支持的默认值写法，暂不额外学习 Annotated。资料：[FastAPI 依赖注入](https://fastapi.tiangolo.com/tutorial/dependencies/)，只看声明依赖与框架调用的基本关系。

### 3. 依赖覆盖：把“原 provider”映射到“测试 provider”

一个不包含需求分析答案的小例子：

```python
def get_label():
    return "real"

def test_label():
    return "fake"

# 假设某路由已经 Depends(get_label)
app.dependency_overrides[get_label] = test_label
```

dependency_overrides 是普通 dict。key 是原 provider **函数对象**，不是字符串 `"get_label"`、类或实例；value 是另一个可调用的 provider，不是直接放 `"fake"`。FastAPI 会执行替代函数，并注入它的返回值。

本日已有替换测试使用：

```python
fake = RecordingAnalyzer(make_fake_output())

def override_analyzer():
    return fake

monkeypatch.setitem(app.dependency_overrides, get_analyzer, override_analyzer)
```

与直接给 dict 赋值相比，pytest 的 monkeypatch.setitem 会在测试结束（包括失败）时恢复原状态，避免影响别的测试。后面测试里的 `lambda: fake` 与上面的无参数函数用途相同：被调用时返回这一个 fake 对象；它不是 fake.analyze 的调用。

已提供的恢复测试用 `with monkeypatch.context() as patch:` 限定覆盖范围，离开 with 块立即恢复，方便在同一个测试中确认真实服务回来。今天理解这段提供好的代码即可，不要求再设计 fixture 或清理框架。

资料：[FastAPI 测试依赖覆盖](https://fastapi.tiangolo.com/advanced/testing-dependencies/)、[pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)。只需上述 key/value 和恢复规则。

### 4. 替换服务，不等于替换 HTTP Response

替身和真实分析器都收到 str，返回 AnalysisOutput，或抛已知异常。它们不返回 Response，也不返回 JSON 字符串。

调用层次是：`Fake.analyze → AnalysisOutput → 路由/框架 → HTTP Response → response.json() 得到 dict`。因此本日仍要断言状态码、JSON 内容和服务调用记录。

已提供的 `RecordingAnalyzer` 把输入追加到 `self.calls`：`fake.calls == [input_text]` 同时检查原文未被改动、恰好调用一次；`fake.calls == []` 才能证明没有调用。只检查 HTTP 200 无法证明替换生效，替身返回结果必须刻意不同于旧 parser 会产生的结果。

### 5. 400 与 503 的区别

| 情况 | 响应 | 含义 |
|---|---|---|
| 得到分析结果，有缺项，strict=False | 200/validation_errors | 草稿分析正常完成 |
| 得到分析结果，有缺项，strict=True | 400/detail.errors | 严格策略拒绝不完整需求 |
| analyze 抛 AnalyzerUnavailable，任意 strict | 503/固定错误 body | 没有获得分析结果，服务暂不可用 |
| text 大于 2000 个字符 | 413 | 路由不调用 analyze |
| JSON、body 或 strict query 不合法 | 422 | 保留框架请求校验 |

503 的完整 HTTP body 固定为：

```json
{
  "detail": {
    "code": "ANALYZER_UNAVAILABLE",
    "message": "Analysis service is temporarily unavailable"
  }
}
```

HTTPException 的 detail 参数只传内层 dict，不再次包 detail。不能直接回显 `str(exc)`、原请求文本或内部诊断，也不打印它们。只捕获 AnalyzerUnavailable；普通 ValueError 等编程错误应继续暴露给测试定位，不要捕获 Exception 后把所有错误都伪装成 503。

## 五个 TODO

只修改 `Week2/day11/app.py`、`Week2/day11/test_day11.py` 和学习记录。service.py、失败演示脚本及 Day 10 的两个错误策略已提供，不改历史日的实现。

### TODO 1：路由真正使用注入的分析器

文件：app.py 的 analyze_requirement。

- 输入：AnalyzeRequest 模型、bool strict、框架注入的 analyzer 对象。
- 保留第一步 `check_text_length(request.text)`。
- 用 `invoke_analyzer(analyzer, request.text)` 获得 output，恰好调用一次，原文不得 strip 或改变换行。
- 把 **output.validation_errors** 与 strict 交给已有 check_business_errors，然后返回这个 output。
- 删除路由里旧的 parse_requirement/validate_result/build_output 调用块与不再使用的相应 import；这些解析步骤现在属于服务对象。
- 正常输出：AnalysisOutput，由框架生成 200；原有 400/413/422 仍保持。不要重新解析输入来覆盖服务结果。
- 完成条件：默认真实服务行为不变；固定替身可以决定响应内容；缺项来自替身输出时默认模式也保留该列表；fake.calls 证明原文转发和只调用一次。

### TODO 2：把已知服务异常转换为 503

文件：app.py 的 invoke_analyzer。

- 输入：分析器对象和 str text。
- 在 try 中执行现有 `analyzer.analyze(text)`，成功则原样返回其 AnalysisOutput。
- 只捕获 AnalyzerUnavailable，将它转换为 HTTPException，status_code=503，detail 使用上一节的固定 code/message。可用 Day 7 学过的 `raise ... from exc` 保留内部原因，但不能将异常文本放入 HTTP body 或自行打印。
- 不捕获 ValueError 或所有 Exception，不返回异常对象，不在 except 后继续解析/伪造成功结果，不重试。
- 完成条件：不可用替身返回精确 503 body，诊断文本不泄露；普通编程错误仍被 TestClient 抛出；正常和失败均不写文件。

完成 TODO 1 后再定位 TODO 2 的错误。Depends 的 provider 构造阶段不在 invoke_analyzer 的 try 范围内，本题不处理 provider 创建失败。

### TODO 3：严格模式下的服务不可用

文件：test_day11.py 的 test_unavailable_in_strict_mode，替换 pytest.fail。

1. 准备 UnavailableAnalyzer，用 monkeypatch.setitem 和返回该对象的 provider 覆盖 get_analyzer。
2. POST，query strict=true，body 为 `{"text": "機能: 登録"}`。
3. 断言状态 **503**、完整 body 等于已有 UNAVAILABLE_BODY、fake.calls 等于 `["機能: 登録"]`。

验证目的：虽然原文看起来缺验收条件，但尚未获得服务的分析结果，不能跳过服务、先拿旧 parser 的缺项报告返回 400。正常拿到缺项结果与服务不可用是两回事。

### TODO 4：超长时根本不调用分析方法

文件：test_over_limit_does_not_call_analyzer，替换 pytest.fail。

1. 使用 UnavailableAnalyzer 并覆盖 provider。
2. POST，strict=true，text 为 `"あ" * 2001`。
3. 断言 413；完整 body 为 `{"detail": {"code": "TEXT_TOO_LONG", "max_length": 2000, "actual_length": 2001}}`；**fake.calls 必须为 []**。

验证目的：如果先调用分析器就会得到 503，而不是先拒绝超长文本。依赖对象可以已经由 provider 创建，这个断言只检查 analyze 没有执行。

### TODO 5：严格策略检查的是服务返回的业务错误

文件：test_strict_checks_injected_business_errors，替换 pytest.fail。

1. 准备 `RecordingAnalyzer(make_incomplete_output())` 并覆盖 provider。
2. POST，strict=true，text 使用已有 VALID_TEXT（原文自身包含完整分类）。
3. 断言 400；完整 body 为 `{"detail": {"code": "REQUIREMENT_INCOMPLETE", "errors": MISSING_ACCEPTANCE}}`；fake.calls 等于 `[VALID_TEXT]`。

验证目的：不能重新解析原文、忽略服务给出的 validation_errors。当前故意让替身输出与旧 parser 不同，才看得出路由究竟使用了谁。

## 学习顺序与测试

- 0～10 分钟：填开始时间，简短复习 dict/list 与 strict 两种模式。
- 10～35 分钟：读 service.py 和 app.py，理解 provider、Depends 和替换测试的完整调用链。
- 35～65 分钟：完成 TODO 1、2，保持既有 API 行为。
- 65～95 分钟：完成三项自写测试，检查返回值、调用次数、拒绝优先级与覆盖恢复。
- 95～120 分钟：真实 HTTP 验证、复盘、自报实际用时；结束时间最后填写。

根目录执行，PowerShell / CMD / Cmder 通用，无需安装新依赖：

```text
.\.venv\Scripts\python.exe -m pytest Week2/day11/test_day11.py -q --tb=short
.\.venv\Scripts\python.exe -m pytest Week2/day10/test_day10.py Week2/day11/test_day11.py -q --tb=short
```

初始预期 Day 11 为 `7 passed, 9 failed`：旧行为仍工作，但路由忽略注入对象，六项提供好的依赖测试会失败；三项自写测试还是 TODO。初始 Day 10～11 合计 `24 passed, 9 failed`。完成全部任务应为 Day 11 `16 passed`、Day 10～11 `33 passed`，全仓目标 `104 passed`。

脚手架实测（2026-09-08）：上述两组初始结果已确认；全仓 `95 passed, 9 failed`，九项失败全部属于 Day 11 的练习，历史 88 项保持通过；`pip check` 通过。正常应用与安装失败 provider 的演示应用均可在独立本机进程启动，200/400/413/422、日文 UTF-8、docs HTML 和 OpenAPI 输入位置检查通过，临时目录无输出文件。503 仍未实现，失败演示暂时返回 200；未将其误报为完成。两个临时验收服务均已停止。

这不是项目安装故障。只完成 TODO 1 后，可能看到 AnalyzerUnavailable 从测试中抛出，那是 TODO 2 尚未处理；不要通过改成 raise_server_exceptions=False、skip/xfail 或删除断言掩盖问题。原有两条间接依赖弃用警告不影响练习，无需处理或屏蔽。

## 真实 HTTP 验证

终端 A（两种 shell 通用）启动正常应用：

```text
.\.venv\Scripts\python.exe -m uvicorn Week2.day11.app:app --host 127.0.0.1 --port 8011 --reload
```

终端 B：

```text
curl.exe -i http://127.0.0.1:8011/health
curl.exe -i -H "Content-Type: application/json" --data-binary "@Week2/day09/sample_request.json" http://127.0.0.1:8011/analyze-requirement
curl.exe -i -H "Content-Type: application/json" --data-binary "@Week2/day10/incomplete_request.json" "http://127.0.0.1:8011/analyze-requirement?strict=false"
curl.exe -i -H "Content-Type: application/json" --data-binary "@Week2/day10/incomplete_request.json" "http://127.0.0.1:8011/analyze-requirement?strict=true"
curl.exe -i -H "Content-Type: application/json" --data-binary "@Week2/day09/invalid_request.json" http://127.0.0.1:8011/analyze-requirement
```

依次预期 200/ok、200/完整日文分析、200/validation_errors、400/detail.errors、422。打开 [Day 11 接口文档](http://127.0.0.1:8011/docs) 确认仍只有 strict query 与 text body，不应要求用户传入 analyzer 对象。

再用单独终端 C 启动已提供的本机失败演示（两种 shell 通用）：

```text
.\.venv\Scripts\python.exe -m Week2.day11.failure_demo
```

该独立进程在 8012 端口临时覆盖 provider。它仅模拟 analyze 抛出异常，不是真的外部服务，也不会修改正常应用进程或创建配置文件。

终端 B 请求失败演示：

```text
curl.exe -i -H "Content-Type: application/json" --data-binary "@Week2/day09/sample_request.json" http://127.0.0.1:8012/analyze-requirement
```

完成 TODO 后应为 503/固定错误 body，不含内部诊断或 traceback。超长在失败演示里仍应优先得到 413：

```text
.\.venv\Scripts\python.exe -c "import requests; s=requests.Session(); s.trust_env=False; r=s.post('http://127.0.0.1:8012/analyze-requirement', json={'text':'x'*2001}, timeout=5); print(r.status_code); print(r.json())"
```

再次请求正常 8011 应仍是原有行为，证明两个进程分离。完成后分别 Ctrl+C 停止两个服务。curl 的进程退出码不等于 HTTP 状态码，要检查响应。

初始脚手架的失败演示仍返回 200，因为路由还没使用注入对象；完成 TODO 1 但未完成 TODO 2 时可能返回 500。最终必须是 503，不能把“服务可启动、docs 写了 503”误认为实现完成。

## 今天不需要学习

真实 LLM SDK/模型选择/密钥、Protocol/抽象基类、Annotated、复杂 DI 容器、缓存与单例生命周期、yield 依赖、异步、数据库、重试、鉴权、全局异常处理或部署。这里只创建轻量对象；未来接真实外部服务时再设计连接生命周期、超时和重试。

## 完成标准

- 本日 16 项、Day 10～11 的 33 项测试通过；三项自写测试包含指定状态码、完整错误结构和调用记录，不用假 HTTP Response 绕开路由。
- 真实服务仍满足 Day 10 的原有契约；注入替身能够控制输出；分析恰好调用一次、输入原文保持；超长时不调用 analyze。
- 只将已知 AnalyzerUnavailable 映射为固定 503，不泄露内部诊断或输入；意外编程错误仍可由测试定位；替换作用域结束恢复真实服务。
- 正常和失败不写输出文件、不请求外部 API；完成 8011/8012 的真实 HTTP 验证、UTF-8 日文、状态码和日志检查。
- 学习后能说明 provider/实例/方法/返回模型的关系、依赖字典的 key/value、400 与 503 的不同，以及不调用 analyze 与不执行 provider 的区别。只在复盘时回答，不要求学前作答。
- 复盘和实际用时记录完成，结束时间放最后一行。告诉我 `Day 11 完成，请检查`；全部验收通过后，按项目规则自动更新进度、提交并推送 GitHub。
