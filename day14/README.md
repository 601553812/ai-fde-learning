# Day 14 — LLM 集成准备：校验模型返回的 JSON

日期：2026-09-12 建立材料，2026-09-13 验收与收尾（日本时间；Day 表示学习序号）。

状态：已完成本日收尾。学习者写完四项代码任务，本日 16 项、全仓 139 项测试通过；助手按用户要求补齐复盘与验收，概念仍待巩固。实际用时未记录。下方 TODO、初始失败和运行步骤保留为原作业与历史过程，不是当前未完成项。

## 最终验收（2026-09-13）

- 助手检查时，decode_requirements、ModelOutputAnalyzer.analyze、502 映射和恢复测试均已由学习者实现，Day 14 直接得到 16 passed。未发现需要代写或修复的功能代码；助手仅清理过时的 TODO 文件说明和测试文件末尾空行。
- 全仓 139 passed，pip check 通过。独立进程验证默认配置、非默认上限、无效配置、模型输出错误后恢复、模拟服务不可用；200/400/413/422/405/502/503、UTF-8、docs/OpenAPI、固定错误结构、无输出文件与服务停止均通过。demo 以 0 退出，显示 502 → 200 和两次调用记录。
- 用户明确表示疲惫，要求助手完成未写部分并结束本日。原复盘答案保留，错题、四题助手参考答案及学习过程见 day14_notes.md；参考答案不等于学习者已独立理解，不再追加追问。
- 下次先用本日一个已有请求简短区分“构造对象、取得模型输出、运行时校验、测试断言”，再根据状态继续学习；不叠加补课。

## 今天要完成什么

给已有 API 接上一段处理模型输出的代码：模型返回 JSON 字符串，程序校验并转换成 RequirementData，再计算业务缺项，最终返回熟悉的 AnalysisOutput。额外实现模型输出错误后的恢复测试。

这是接真实 LLM 前的一步。本日全部本地运行，LocalModelClient 实际调用旧规则解析器生成模拟 JSON，FixedModelClient 返回指定文本；两者都没有模型推理能力、网络请求或费用。今天的成果证明“输出处理链可工作”，不代表已接入或评测真实模型。下一步再选择真实服务并接入其 API。

先阅读非测试代码，顺序为 model_client.py → service.py → app.py。无需重新做 Day 13 的复盘题。

## 最小知识

### 1. 三种对象各自负责什么

| 代码 | 输入 | 输出 | 职责 |
|---|---|---|---|
| ModelClient.generate | 用户需求 str | 模型返回的 JSON 文本 str | 取得模型输出；今天由本地替身完成 |
| decode_requirements | JSON 文本 str | RequirementData | 检查 JSON 和字段类型 |
| ModelOutputAnalyzer.analyze | 用户需求 str | AnalysisOutput | 串起模型调用、结构校验和业务检查 |

generate 是本项目约定的方法名，不是 Python 内置功能或某个 SDK API。ModelClient 的方法签名类似 Java 中约定的接口方法；这里用普通基类表达，没有引入 ABC/Protocol，也没有 Java interface 的编译期约束。

目标调用顺序：HTTP 请求 → 配置/长度检查 → analyzer.analyze(request.text) → client.generate(text) → decode_requirements(raw) → validate_result(...) → AnalysisOutput → strict 业务策略 → HTTP 响应。

这里存在两份不同文本：用户原文 text 和模型返回的 raw。比如用户输入“导出需求”，模型可能返回 `{"functions":["CSV出力"]}`。analyze 要检查 raw，不能继续解析用户原文来假装模型调用成功。

### 2. JSON 字符串怎样变成对象

今天新增的 API 是 model_validate_json。它把 JSON 文本解析并按 Pydantic 模型校验，成功返回模型对象，失败抛 ValidationError。你之前用的 model_validate 接收的是 Python 数据，例如 dict。

独立小例子（不是作业答案）：

```python
from pydantic import BaseModel, ValidationError

class Label(BaseModel):
    name: str

label = Label.model_validate_json('{"name":"検索"}', strict=True)
print(label.name)
print(label.model_dump())  # Python dict
```

若把 name 改成数组，就不符合 str 约定。这里由 Pydantic 执行运行时校验；不是 Python 类型标注自身进行校验。类似 Java 中 JSON 映射工具把文本转为 DTO 并检查结构，具体校验规则取决于工具与配置。

当天只用 model_validate_json(raw, strict=True)、ValidationError、model_dump()。这里 strict=True 控制 Pydantic 类型校验，和 URL 的 ?strict=true 业务开关是两个独立参数；即使 URL 没开严格业务模式，也必须校验模型返回的结构。

依据：[Pydantic JSON 解析](https://docs.pydantic.dev/latest/concepts/json/)、[模型校验方法](https://docs.pydantic.dev/latest/concepts/models/#validating-data)。本节已筛选所需内容，无需通读官方页面。

### 3. 复用现有 RequirementData 的约定

模型输出直接包含 functions、acceptance_criteria、risks、questions、unknown，值为字符串数组。它没有外层 requirements，也不包含 schema_version 或 validation_errors；这些由我们的服务组装。

- `{"functions":["CSV出力"],"acceptance_criteria":["3秒以内"]}`：结构合法。
- `{}`：结构也合法。现有 RequirementData 给五个字段设置了空列表默认值，因此不能另加“缺字段就是格式错误”的规则。
- `{"functions":"CSV出力"}`：functions 不是数组，结构错误。
- `{"functions":[123]}`、`{"functions":null}`：字段值不符合类型。
- `[]`、`null`：顶层不是要求的对象。
- `{"validation_errors":[]}`：这是多余字段，现有 extra="forbid" 会拒绝。
- 自然语言、截断 JSON、包着 Markdown 代码围栏的文本：不符合本题“完整 JSON 文本”契约，拒绝即可，不尝试修复或截取。

模型结构合法后，调用 validate_result(requirements.model_dump()) 得到业务缺项列表。validate_result 的参数需要 dict，所以在这里用 model_dump。AnalysisOutput 的 requirements 字段则可以直接接收 RequirementData 对象。

### 4. 三类错误怎样区分

| 具体场景 | 检查位置 | 本题结果 |
|---|---|---|
| 客户端发送 `{"text":123}` | FastAPI 请求模型 | 422 |
| 客户端请求合法，模型返回 `not-json` | 模型输出校验 | 502 / MODEL_OUTPUT_INVALID |
| 模型返回 `{}` | 结构通过，业务缺功能/验收条件 | 默认 200 + validation_errors；URL strict=true 时 400 |

502 是本练习对上游模型输出错误的 HTTP 约定，Pydantic 本身只抛异常，不决定 HTTP 状态码。已有配置错误/分析服务不可用仍保持各自的 503，超长仍为 413。

服务层用 InvalidModelOutput 表达这一错误；HTTP 层捕获它并返回固定错误 JSON。只捕获明确的异常类型，TypeError 等编程错误继续暴露以便定位。

### 5. 保留原因与对外提示

遇到 ValidationError 时，抛出固定信息的 InvalidModelOutput，并用 `raise 新异常 from 原异常` 保留原因（复用 Day 8）。例如独立的整数转换场景：

```python
try:
    number = int("bad")
except ValueError as error:
    raise RuntimeError("Cannot read number") from error
```

`__cause__` 用于程序内部追踪；API 返回固定 message。原异常可能带输入片段，不应把 str(error)、raw 或完整异常链写进公开响应/学习日志。依据：[Python 异常链](https://docs.python.org/3.11/tutorial/errors.html#exception-chaining)。

## 四项 TODO

### TODO 1：decode_requirements

修改 service.py。输入 raw: str，输出 RequirementData。

1. 调用 RequirementData.model_validate_json(raw, strict=True)。
2. 成功返回所得对象。
3. 只捕获 ValidationError；抛 InvalidModelOutput(MODEL_OUTPUT_ERROR_MESSAGE)，使用 from 保留本次捕获的错误。

不默认返回空对象、不打印原输出、不改变旧模型。通过四项 test_decode... / test_invalid_json... / test_wrong_structure... 测试即完成本项；结构和空默认值的完整契约见上节。

### TODO 2：ModelOutputAnalyzer.analyze

修改 service.py，替换临时的 super().analyze(text)。输入用户原文 str，输出 AnalysisOutput。

1. 调用 self.client.generate(text) 恰好一次，保存返回的 raw。
2. 把 raw 交给 decode_requirements，得到 requirements 对象。
3. 把 requirements.model_dump() 交给 validate_result，得到 validation_errors 列表。
4. 返回 AnalysisOutput(requirements=对象, validation_errors=列表)，版本沿用默认 1.0。

本层不要捕获 InvalidModelOutput、AnalyzerUnavailable 或 TypeError，也不要提前执行 URL strict 策略。完成条件：结果来自模型响应、保留原文调用记录、空数据生成两项业务错误、服务不可用与编程错误向外传播。

### TODO 3：输出无效时返回固定 502

修改 app.py 的 analyze_requirement，仅在 invoke_analyzer 调用附近增加异常处理。

- 长度检查仍在调用前；成功后仍执行 check_business_errors 并返回 output。
- 捕获 InvalidModelOutput，抛 HTTPException(status_code=502, detail=下列对象)，用 from 保留原因。
- detail 为 `{"code":"MODEL_OUTPUT_INVALID","message":"Model returned invalid output"}`。
- 不要把 detail 再包一层；不要把 str(error) 或原始输出放进去。

完成条件：test_route_maps_only_model_output_error_to_502 通过；既有 200/400/413/422/503 行为保持不变。HTTP 层代码已提供其余部分。

### TODO 4：模型输出错误后的下一次请求

修改 test_day14.py 的 test_invalid_model_output_then_success_keeps_both_calls，替换 pytest.fail。需要独立实现以下步骤：

1. monkeypatch.delenv(ENV_NAME, raising=False)，使用默认长度配置。
2. 建立并保存 fake = FixedModelClient("not-json")。用具名函数返回 ModelOutputAnalyzer(fake)，通过 monkeypatch.setitem 覆盖本日导入的 get_analyzer。
3. POST INPUT_A，断言 502、完整 body 等于 MODEL_ERROR_BODY，并断言 fake.calls == [INPUT_A]。
4. 改为 fake.raw = MODEL_JSON；同一个 fake 不清空记录、不重新创建。POST INPUT_B。
5. 断言 200、完整 body 等于 EXPECTED_OUTPUT、fake.calls == [INPUT_A, INPUT_B]。

本 case 的常量已明确给出：INPUT_A 是 CSV 出力需求，INPUT_B 是検索需求，MODEL_JSON 是与二者不同的固定模型结果。第一次产生坏输出前 generate 已经执行，所以也记录了 INPUT_A。能恢复不表示第一次没调用过。

## 运行和手动验证

建议时间：读最小知识和非测试代码 25 分钟；三项实现 35～45 分钟；恢复测试 20 分钟；手动检查与复盘 10～20 分钟。

在项目根目录执行，PowerShell / CMD / Cmder 通用。只用根 .venv，无新增依赖。

先跑今天的测试：

```text
.\.venv\Scripts\python.exe -m pytest day14/test_day14.py -q --tb=short
```

完成后再跑 Day 13～14 回归（检查今天是否影响昨天）：

```text
.\.venv\Scripts\python.exe -m pytest day13/test_day13.py day14/test_day14.py -q --tb=short
```

初始有预期失败：decode_requirements 和恢复测试尚未实现，analyze 暂时沿用规则路径，502 映射尚未添加。数量在下方“脚手架验证”记录；目标为本日 16 项、Day 13～14 共 30 项、全仓 139 项通过。测试失败不等于环境损坏；不修改已有测试或 skip/xfail 绕过 TODO。

手动启动本地模拟服务：

```text
.\.venv\Scripts\python.exe -m uvicorn day14.app:app --host 127.0.0.1 --port 8014
```

另开终端：

```text
curl.exe -i http://127.0.0.1:8014/health
curl.exe -i -H "Content-Type: application/json" --data-binary "@day14/sample_request.json" http://127.0.0.1:8014/analyze-requirement
.\.venv\Scripts\python.exe -c "import requests; s=requests.Session(); s.trust_env=False; r=s.post('http://127.0.0.1:8014/analyze-requirement', json={'text':123}, timeout=5); print(r.status_code); print(r.json())"
```

依次应为 200/ok、200/日文结构化结果、422。配置依然沿用 Day 13；若以前的实验终端还设置了 AI_FDE_MAX_TEXT_LENGTH，先在该终端清理后再启动服务。/docs 可查看输入和响应说明。

默认 LocalModelClient 只生成合法 JSON。要观察真实的“坏输出 → 恢复”，完成 TODO 后运行下方脚本；它用 TestClient 执行本地 API，打印两次响应和模型调用记录，不连接真实 LLM：

```text
.\.venv\Scripts\python.exe -m day14.demo
```

完成后脚本应打印 502 → 200，调用记录为两个不同原文，并以 0 退出；脚手架阶段会非零退出，属于待完成行为。真实 HTTP 服务最后用 Ctrl+C 停止。没有输出文件，脚本只写终端。

## 脚手架验证

- 初始脚手架实测：本日 5 passed / 11 failed，全仓 128 passed / 11 failed；历史 123 项全部通过。11 项失败均对应四个 TODO，包含尚未拦截的 InvalidModelOutput，因此部分报错会经过较长的框架调用栈。
- pip check 通过；已有两条间接依赖弃用警告不影响作业。真实 HTTP 的 200/400/413/422/405、2000/2001 字符边界、日文 UTF-8、docs/OpenAPI 通过，临时目录无输出文件，服务已停止。
- 当前 demo 实测在“第一次应为 502”的断言处非零退出，属于预期 TODO，尚未表示输出处理已完成。
- 助手另在独立进程内用临时参考函数验证了 15 项已提供测试和 demo 的 502 → 200、两次调用记录；参考函数没有写入作业文件。该结果仅证明练习契约可实现，不能作为学习者已完成的证据；最后一项自写测试仍待学习者实现。
- 作业只保存在本地，完成验收后再提交上传。

## 今天不需要学习

真实模型账号/SDK/密钥、Prompt 优化、供应商的 Structured Outputs 请求格式、自动 JSON 修复、重试、流式输出、token/成本计算、RAG、异步或新的依赖注入机制。今天的本地校验不承诺模型事实正确，也不代表真实供应商的生成约束。

学完在 day14_notes.md 回答四个具体场景，填写自报用时，最后填写结束时间。说“Day 14 完成，请检查”后再验收与上传。
