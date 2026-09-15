# Day 14 学习记录

## 学习开始

- 开始时间：1000
- 环境确认：根 .venv；本日使用本地模拟，不需要账号、密钥或新增依赖。

## 本日学习目标（无需提前作答）

- 区分用户原文、模型 JSON 文本、RequirementData、AnalysisOutput。
- 结构校验后再检查业务缺项；给模型格式错误提供固定 502 响应。
- 验证同一个模型替身先返回错误、后返回正确文本的两次调用。

## 学习后复盘

1. 验证点：输入与模型输出不是同一份数据。看 test_day14.py 的 test_analyzer_uses_model_text_instead_of_reparsing_input：发送 INPUT_A（CSV 需求），fake 返回 MODEL_JSON（functions 为“モデル側の固定結果”）。最终 functions 应取哪一份？请指出 analyze 中取得模型文本和校验它的两处调用。

答：モデル側の固定結果   取得模型文本是ModelOutputAnalyzer(fake)  校验是assert output.model_dump() == EXPECTED_OUTPUT

2. 验证点：区分错误发生在哪一端。场景 A：客户端 POST {"text":123}；场景 B：客户端 POST {"text":INPUT_A}，fake 返回 "not-json"；场景 C：客户端 POST {"text":INPUT_A}，fake 返回 "{}"，URL strict=true。分别填写状态码和拒绝原因即可。

答：503 AI_FDE_MAX_TEXT_LENGTH must be an integer from 1 to 10000  502 Model returned invalid output  200

3. 验证点：失败时模型是否已经执行。看 test_invalid_model_output_then_success_keeps_both_calls：同一 fake 先返回 "not-json" 接收 INPUT_A，再改成 MODEL_JSON 接收 INPUT_B。写出两次请求结束后的 calls 列表，并指出是哪行代码记录第一次输入；和配置 bad 导致的拒绝相比，执行位置有什么不同？

答：INPUT_A INPUT_A,INPUT_B

4. 验证点：内部原因与对外响应的区别。看 test_invalid_json_keeps_validation_error_as_cause，异常的 __cause__ 应是什么类型？API 是否应该把这个原异常的完整内容发给客户端？各用一句话说明。

答：

## 验收记录（学习后填写）

- 自动测试结果（助手验收）：检查时四项代码已写完，本日 16 passed；全仓 139 passed；pip check 通过。两条既有间接依赖弃用警告不影响结果。
- 本地演示 502 → 200 与 calls（助手验收）：demo 退出码 0；第一次 [INPUT_A]，第二次 [INPUT_A, INPUT_B]，顺序及两次完整响应均正确。
- 真实 HTTP（助手验收）：默认 2000 和配置 12 的边界、配置无效 503、坏输出 502 后成功 200、模拟服务不可用 503 均通过；原有 strict 400、请求/query/JSON 422、错误方法 405、日文 UTF-8、docs/OpenAPI 通过。五个临时服务已停止，临时目录无生成文件，服务日志无 traceback。

## 错题本

以下区分“日志中发生过、学习者已修正的错误”和“复盘表述中待巩固的概念”，不把空白回答当成答错。

### 1. response.json 少写调用括号（日志证实，学习者已修正）

错误写法：

```python
assert response.json == MODEL_ERROR_BODY
```

正确写法：

```python
assert response.json() == MODEL_ERROR_BODY
```

原因：response.json 是方法对象；加 () 才执行方法并拿到 JSON 解码后的数据。本次日志明确显示在恢复测试中比较方法与字典导致 AssertionError，实际 HTTP 状态已是 502，不能据此判断路由返回状态错误。

最小示例：`data = response.json()` 后再比较 `data == MODEL_ERROR_BODY`。与 Depends(get_analyzer) 需要传递函数本身的场景区分：这里需要的是方法的执行结果。

### 2. 完成断言后残留 pytest.fail 占位（日志证实，学习者已修正）

错误写法：

```python
assert response.status_code == 200
pytest.fail("TODO 4: bad model output followed by valid output")
```

正确写法：保留真实断言，删除已经被实现替换的 pytest.fail 占位。

原因与最小示例：`assert True; pytest.fail("unfinished")` 仍会失败，因为 pytest.fail 无条件标记失败。此记录属于练习收尾遗漏，不据此推断业务逻辑理解错误。

### 3. 构造对象、取得输出、校验、测试断言混淆（复盘第 1 题）

原答正确指出最终 functions 来自模型固定结果，但将 ModelOutputAnalyzer(fake) 说成“取得模型文本”，将 assert 说成程序中的校验。

准确对应：

```python
analyzer = ModelOutputAnalyzer(fake)   # 构造对象并保存 client
raw = self.client.generate(text)      # analyze 内取得模型返回的文本
requirements = decode_requirements(raw)  # analyze 内执行结构校验
assert output.model_dump() == EXPECTED_OUTPUT  # 测试检查最终结果
```

这是位置对照，以上代码不需要拼成一个函数直接运行。最小调用例子：先 `analyzer = ModelOutputAnalyzer(fake)`，再 `output = analyzer.analyze(INPUT_A)`；构造函数只保存 fake，generate 是执行 analyze 时才调用。

### 4. 请求错误、服务器配置错误与严格业务模式混淆（复盘第 2 题）

在服务器配置合法、输入长度未超限的前提下：

- 错误判断：客户端发送 text=123 应为 503。正确：422，因为 AnalyzeRequest 要求 text 是字符串；配置错误才使用另一个 503/CONFIGURATION_INVALID 分支。此前原答写的配置转换消息是内部 ConfigurationError 信息，也不是该 503 的公开 message。
- 原答正确：客户端请求合法、模型返回 not-json 时为 502，公开 message 为 Model returned invalid output。
- 错误判断：模型返回 {} 且 URL strict=true 时为 200。正确：{} 能通过结构校验并得到空列表，但业务检查发现缺少功能和验收条件，严格业务模式因此返回 400。

最小对照：同样是模型输出 {}，URL 默认 strict=false 为 200 并带 validation_errors；URL strict=true 为 400 并带 detail.errors。Pydantic 的 strict=True 控制结构/类型校验，不替代 URL 的业务开关。

原题没有重复注明服务器环境已清理；以上订正明确采用合法配置前提。如果人为同时设置无效配置，还需要按具体执行过程判断，不能仅凭 text=123 推断全部场景。

## 助手参考答案（按用户要求补齐，本日不再追问）

以下为参考说明，原始答案保留在上方，不作为已独立掌握的证据。

1. functions 取模型的“モデル側の固定結果”，这一点原答正确。取得文本是 `self.client.generate(text)`，结构校验入口是 `decode_requirements(raw)`，内部调用 `RequirementData.model_validate_json(raw, strict=True)`。`ModelOutputAnalyzer(fake)` 只是构造分析器对象；测试中的 assert 用来检查运行结果。
2. 假设配置合法且没有超长：A 为 422（客户端 text 类型错误）；B 为 502（模型输出不是合法 JSON）；C 为 400（空对象通过结构校验，但严格模式拒绝业务缺项）。模型结构合法不保证业务完整。
3. 第一次结束是 `[INPUT_A]`，第二次结束是 `[INPUT_A, INPUT_B]`，原答已表达正确的内容和顺序。记录发生在 `FixedModelClient.generate` 的 `self.calls.append(text)`；坏 JSON 是 generate 返回后才发现，所以第一次也有记录。配置 bad 则在取得配置时拒绝，尚未执行 generate，因此不会追加调用。
4. 在 `test_invalid_json_keeps_validation_error_as_cause` 中，InvalidModelOutput 的 `__cause__` 是 Pydantic 的 ValidationError。API 不返回其完整内容，因为可能带原始输入片段；本题只返回固定 code/message。`raise ... from error` 保留内部原因，不意味着要把原因序列化进 HTTP 响应。该题原本未填写，由助手补充。

## 学习过程与贡献记录（2026-09-13）

- 学习者已完成全部四项代码任务；助手开始检查时本日测试已全通过，功能代码无需补写。助手完成剩余验收、参考复盘、错题整理和文档收尾。
- Cmder 有四轮完整 pytest 结果：15 passed/1 failed（response.json 少括号）→ 15 passed/1 failed（残留 pytest.fail）→ 16 passed → Day 13～14 合并 30 passed。只统计有完整结果的执行，不重复计数终端重绘。
- 日志还能确认真实 HTTP 的 200/422、服务器正常关闭，以及 demo 的 502 → 200、两次调用列表和退出码 0。日志不能证明编辑器中的具体修改步骤或学习者当时思考。
- 开始时间 1000 为学习者原填值，保留；材料在 2026-09-12 建立，本次验收日期为 2026-09-13。未填写实际用时，不用日志跨度或起止差值推算。
- 学习者表示“没有完成……今天就这样吧，实在撑不住了”，授权助手补全并收尾。代码成果验收通过与概念待巩固分别记录；下次只从第 1 题的一段现有调用链简短复习，不追加本日任务。

## 学习反馈

- 难度、内容量、仍需讲解的具体位置：原栏未填写；本次对话表示疲惫，选择助手补齐复盘并结束。暂不据此判断整体练习量过多或减少后续全部内容。
- 实际用时（排除中断，自行填写）：未记录（学习者未填写，不以日志估算）。

- 结束时间：未记录（学习者未填写；本日于 2026-09-13 按用户要求收尾）。
