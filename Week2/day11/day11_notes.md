# Day 11 学习记录

## 学习开始

- 开始时间：1938
- 环境确认：根目录 `.venv`，无需新增依赖或 API 密钥：
OK
开始时只填写以上内容；结束时间在完成复盘后于最后一行填写。

## 本日学习目标（无需提前作答）

- 先复习 requirements 是 dict、分类值是 list；缺业务项时 strict=False 返回 200，strict=True 返回 400。
- 跟踪 provider 函数、分析器对象、analyze 方法、AnalysisOutput、HTTP Response 各自是什么。
- 用 Depends 接入可替换的分析器，用依赖覆盖测试可控结果和失败。
- 保留旧接口行为，实现服务不可用时的安全 503；不把普通编程错误伪装成 503。

## 学习后复盘

1. 对本题写出调用链：FastAPI 调用哪个 provider？provider 返回什么？路由调用什么方法？方法返回什么？
FastAPI调用RuleBasedAnalyzer RuleBasedAnalyzer返回AnalysisOutput 路由调用analyze_requirement 返回AnalysisOutput
2. 为什么 Depends(get_analyzer) 不写成 Depends(get_analyzer())？这里传入函数与调用函数的区别是什么？
因为需要传入函数而不是对象 传入函数就是依赖函数 调用函数就会传入函数的返回值
3. 替换成功后，如果路由仍直接调用旧 parser，哪个测试会发现？仅断言状态码 200 为什么不够？
test_unavailable_in_strict_mode会发现
4. 同样是 strict=True，拿到业务缺项结果时为什么是 400，而分析器抛 AnalyzerUnavailable 时为什么是 503？
check_business_errors中定义了如果业务缺项就是400  因为被替换成了UnavailableAnalyzer 你这个问题我真的没搞明白你想问什么
5. 输入 2001 字符时，fake.calls 应是什么？这只能证明 analyze() 没调用，还是也证明 provider 没执行？
是list
6. dependency_overrides 的 key/value 分别是什么？为什么要在测试结束后恢复？monkeypatch.setitem 在这里帮了什么忙？

7. 为什么只捕获 AnalyzerUnavailable，不捕获所有 Exception 并返回 503？为什么不把 str(exc) 放进错误 body？

8. 三项自写测试各自的输入、状态码、完整响应或调用次数断言；最终自动测试结果：

9. 手动验证：真实 200/400/413/422、临时失败替身的 503、覆盖恢复、日文响应、日志和无输出文件结果：

10. 不理解的点、需要复习的内容，以及日语说明（3～5 句，向同事说明可替换服务和 400/503 的区别）：

## 助手参考答案与本日收尾（2026-09-09）

学习者明确要求直接提供复盘答案并结束当天。以上原答案和反馈全部保留；以下由助手补充，不代表学习者已经独立掌握。今天不再追问，下一次只从一个已有案例重新梳理。

### 1. 调用链

FastAPI 处理请求时，看到 `Depends(get_analyzer)`，先调用 **get_analyzer 函数**；这个函数返回 **RuleBasedAnalyzer 对象**，不是 AnalysisOutput。FastAPI 再调用 analyze_requirement，把该对象放进 analyzer 参数。路由经 invoke_analyzer 调用 **analyzer.analyze(text)**，这一步才返回 **AnalysisOutput**。最后路由返回该模型，由 FastAPI 转为 HTTP JSON 响应。

简记：get_analyzer 提供对象；对象的 analyze 方法产生结果。测试覆盖生效时，提供对象的函数换成返回 fake 的函数，其他调用层次不变。

### 2. 函数与调用函数

原答案方向正确。`get_analyzer` 是函数本身，交给框架在处理请求时调用；`get_analyzer()` 是立即执行函数，得到分析器对象。Depends 这里需要的是可调用函数，不是这次执行得到的普通分析器实例。类型标注本身不负责创建对象，普通 Python 直接调用路由函数也不会自动完成 FastAPI 的依赖处理。

### 3. 如何证明替换有效

最直观的是 test_override_controls_output_and_receives_exact_text：它要求返回预设的替身结果，而不是从输入真正解析的结果，同时检查 fake.calls。test_override_scope_restores_real_service 也会检查临时范围内返回替身结果。原答案提到的 test_unavailable_in_strict_mode 同样能揭露绕过失败替身的问题：应该得到 503，如果直接用旧 parser，可能先得到 400。只看 200 不够，因为真假分析器都可能正常返回 200；必须检查具体结果或调用记录。

### 4. 为什么分别是 400 和 503

题目想区分的是“已经分析出结果，但结果不满足严格业务要求”和“分析根本没能完成”。前者有缺项列表，strict=True 时按本项目约定返回 400；后者抛 AnalyzerUnavailable，尚未获得分析结果，因此返回 503 表示暂不可用。strict 只决定如何处理已经得到的业务缺项，不能把服务不可用变成业务缺项。UnavailableAnalyzer 只是测试中模拟失败的方式，不是 503 的业务含义。

### 5. 超长输入与 calls

预期是 **空列表 `[]`**，不仅是“list 类型”。长度检查先拒绝 2001 字符，analyze 没有执行，因此没有调用记录。它不证明 get_analyzer 或替代函数没执行：FastAPI 可以先取得对象，然后路由才检查长度。“创建/取得对象”和“调用对象的 analyze 方法”是两件事。

### 6. 替换字典与恢复

key 是原函数对象 get_analyzer；value 是替代函数，例如 `lambda: fake`，调用它会返回已准备好的 fake。不是把 get_analyzer() 返回的对象放在 key，也不是直接把 fake 放在 value。恢复是为了不影响后面的请求和测试。monkeypatch.setitem 修改字典并记录原状态，测试结束时自动撤销；本日 with monkeypatch.context() 范围更小，离开 with 就撤销。original 只是备份，assert 只是检查，真正恢复由 context 的退出处理完成；断言失败时也会执行清理，但失败后不会继续执行后面的普通语句。

### 7. 只捕获预期异常，不泄露内部信息

AnalyzerUnavailable 是约定好的暂时不可用情况，可以转换成 503。TypeError、ValueError 等可能是代码错误，若全部捕获成 503，会隐藏真正的问题。异常字符串可能包含内部地址、请求内容或其他敏感信息，因此对外只提供固定 code/message；`raise ... from error` 可以在内部保留异常原因，不等于把原因直接返回给客户端。

### 8. 三项自写测试及自动验证

- test_unavailable_in_strict_mode：失败分析器；输入“機能: 登録”，strict=true；返回 503，完整响应等于 UNAVAILABLE_BODY，fake.calls 为 `["機能: 登録"]`。证明即使原文缺项，也不能绕过服务先返回 400。
- test_over_limit_does_not_call_analyzer：失败分析器；输入 `"あ" * 2001`，strict=true；返回 413，detail 为 `{"code": "TEXT_TOO_LONG", "max_length": 2000, "actual_length": 2001}`，fake.calls 为 `[]`。证明先检查长度，不调用分析方法。
- test_strict_checks_injected_business_errors：替身返回缺少验收条件的结果；输入本身完整的 VALID_TEXT，strict=true；返回 400，detail 为 `{"code": "REQUIREMENT_INCOMPLETE", "errors": MISSING_ACCEPTANCE}`，fake.calls 为 `[VALID_TEXT]`。证明严格策略检查替身返回的错误，而不是重新解析原文。
- 助手验收：Day 10～11 合计 **33 passed**（Day 11 的 16 项全部包含在内）；全仓 **104 passed**；pip check 通过。两条已有间接依赖弃用警告保留，不属于本日失败。

### 9. 助手代做的手动验证

在两个独立本机进程、临时工作目录中验证真实 HTTP：正常 200、strict 缺项 400、超长 413、格式/参数错误 422、错误方法 405、失败替身在两种 strict 模式下均返回固定 503；失败服务收到超长输入仍先返回 413。2000 字符边界允许，日文 UTF-8 和完整结果结构正确，docs/OpenAPI 正常且不要求客户端提供 analyzer。安装失败替身不影响正常进程，正常进程错误后仍能成功；临时目录无输出文件，服务日志无 traceback。两个验收进程已停止。覆盖范围结束后恢复真实行为由自动测试验证。以上为助手验证，不冒充学习者操作。

### 10. 待巩固与日语参考说明

待巩固：路由选择函数、get_analyzer 提供对象、analyzer.analyze 返回模型、client.post 返回 Response 四者的区别；其次才是 with 范围内的替换与恢复。下次先围绕 test_override_scope_restores_real_service 的一个请求讲清这些对象，不先增加新库或新题。

日语参考（无需今天背诵）：

この API は、受け取った要件テキストを分析器に渡し、構造化した結果を返します。
テストでは分析器を一時的に差し替え、成功や障害を再現します。
分析結果に必須項目の不足があり、厳格モードの場合は 400 を返します。
分析処理が一時的に利用できない場合は、内部情報を含めずに 503 を返します。
テスト後は差し替えを解除し、通常の分析器に戻します。

## 错题本

出现典型错误后追加：错误写法、正确写法、原因、最小示例。

### 本日已修正的典型错误

1. **重复调用并漏参数**：错误是在 invoke_analyzer 已经分析后再次写 `analyzer.analyze()`；正确是保留第一次调用返回的 output，不再调用第二次。原因：analyze 必须接收 text，而且一次请求只应分析一次。最小对照：`output = invoke_analyzer(analyzer, text)` 后使用 output，而不是再执行 `analyzer.analyze()`。
2. **混淆分析器和 HTTP 响应**：错误是 `response = client.post(...); response.calls`；正确是对响应检查 status_code/json，对保存好的分析器对象检查 `fake.calls`。原因：Response 不提供该测试替身自定义的 calls 属性。最小对照：`fake.calls == [text]` 与 `response.status_code == 200` 检查的是两个不同对象。
3. **503 错误结构不匹配**：错误是 `{"code": "Analyzer unavailable", "errors": []}`；正确是 `{"code": "ANALYZER_UNAVAILABLE", "message": "Analysis service is temporarily unavailable"}`。原因：code 是固定协议值，不能用自然语言近似替代，字段也必须符合约定；作为 HTTPException 的 detail 传入时，不再手动套一层 detail。
4. **把函数执行结果当替换字典的 key**：错误是 `app.dependency_overrides[get_analyzer()] = ...`；正确是 `app.dependency_overrides[get_analyzer] = ...`。原因：FastAPI 按 Depends 中保存的原函数对象查找替换规则，而不是按分析器实例查找。

### 学习过程证据与掌握状态

- 当前代码和测试已经修正上述问题。当天可用 Cmder 日志包含 analyze 缺 text 的重复报错，以及后续 16 passed、33 passed 的结果；这里只记录可见证据，不推断完整尝试次数或编辑器内的修改过程。
- 助手检查过程中先见 5 passed / 11 failed，修正后 Day 10～11 为 33 passed、全仓为 104 passed。不能把多个测试在同一行失败当成同样数量的独立知识错误。
- 本日按学习者要求结束：代码验收通过，参考复盘已提供；学习者明确反馈尚不能消化，不记录为已经独立掌握。实际用时采用下方自报 2h，结束时间保留 2115，不从日志或起止时间重算。

## 学习反馈

- 今天的量：偏少 / 合适 / 偏多，原因：偏难 完全消化不了
- 实际用时（排除中断，自行填写）：
2h
- 结束时间：2115
