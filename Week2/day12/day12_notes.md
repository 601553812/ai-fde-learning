# Day 12 学习记录

## 学习开始

- 开始时间：2229
- 环境确认：根目录 .venv，无需安装新依赖：
OK
## 本日学习目标（无需提前作答）

- 已经梳理：analyze 接收 str，返回 AnalysisOutput；requirements 是 RequirementData，内部字段是 list，validation_errors 也是 list。
- 接下来只练习：提供对象的函数、真实对象与替身切换、两次请求的调用记录。
- 不要求重新回答昨天的十道题，不把昨天的参考答案当成已经掌握。

## 学习后复盘（只答三题，可以在对话中说）

1. 在恢复测试中，get_test_analyzer 返回什么？fake.analyze 返回什么？client.post 返回什么？用三个变量名和对象类型说明即可。
FixedAnalyzer对象 返回AnalysisOutput 返回Response
2. 两次请求后，fake.calls 应有什么内容？如果每次 analyze 都先清空 calls，这个断言会发现什么问题？
INPUT_A和B都被记录在calls里了 如果每次都清空的话 最后只剩下最后一条 也就是B 这个断言会发现list里的元素数量都不匹配
3. 为什么同样的 INPUT_A，在 with 内得到固定结果，离开 with 后得到 CSV出力？不要求背术语，说明替换规则何时生效、何时撤销即可。
因为在with作用域内 get_analyzer被替换成了get_test_analyzer 而离开with之后他又是他自己了
## 验收记录

- 自动测试结果：all passed
- 两次请求是否都得到固定结果、调用记录是否保持原文与顺序：应该没问题
- 离开临时范围后是否恢复真实结果：恢复了

## 错题本

仅在出现需要记录的错误时补充：错误写法、正确写法、原因和最小示例。

## 验收补充（2026-09-10）

- 原作业验收通过：Day 12 的 5 项、Day 11～12 的 21 项、全仓 109 项测试全部通过；pip check 通过。两条已有依赖弃用警告不影响结果。
- 实现检查：analyze 追加原文并返回已保存的 AnalysisOutput；两次 POST 使用不同输入，对各自完整 JSON 和状态码分别断言，fake.calls 精确比较 `[INPUT_A, INPUT_B]`，没有只检查数量或只检查最后一条。
- 手动补充验证：在独立进程、临时工作目录运行观察脚本，退出码 0，UTF-8 日文输出正确，无 traceback、无输出文件；正常请求使用固定结果，超长请求返回完整 413，提供对象次数与 analyze 次数分开记录，离开临时范围后恢复真实 CSV出力。未启动网络监听端口，TestClient 请求只在本机进程内处理。
- 学习过程：当天 Cmder 中四轮可见完整测试结果为 `2 passed / 3 failed → 4 passed / 1 failed → 5 passed → 21 passed`。前两轮失败对应尚未完成的 NotImplementedError/测试占位，不据此新增概念错题；终端重绘中的重复命令不算额外完整执行。用时仅采用下方自报 20min。
- 复盘第 1 题正确区分 FixedAnalyzer、AnalysisOutput、Response；第 2 题正确指出清空记录会只剩 INPUT_B，补充：当前列表精确比较同时检查数量、内容和顺序。第 3 题对临时生效与恢复的理解正确，术语补准：不是 get_analyzer 的函数代码被改写，而是 FastAPI 处理 Depends 时按字典临时选择 get_test_analyzer；直接调用原函数仍执行原函数。

## 按本人要求追加的复习（不影响原作业已完成）

- 反馈：今天内容较少，愿意继续增加一点或理清昨天的疑问。按自报 20min 和本次正确实现/复盘判断，原作业偏轻；不把昨天的吃力等同于今天仍需要同样低负荷。
- 新增 review_day11.md 与 review_flow.py，围绕“覆盖只影响框架选择”和“取得对象不等于执行分析”做分段观察；另提供一项可选测试，验证先成功、再超长时旧调用记录保留且不新增。
- 材料建立时仅完成助手编写和验证，未当作学习者已完成追加复习；后续口头确认见下。追加时长未记录，原作业 20min 和结束时间 2248 保持不变；如继续记录实际投入，另报追加时长，不从时钟差计算。
- 追加复习口头确认：学习者已说明 Depends(get_analyzer) 把提供对象的函数交给 FastAPI，由框架在处理请求时调用，并将结果传入路由的 analyzer 参数；也明确区分传函数与立即调用函数。助手补准：get_analyzer 当前创建新对象，但提供函数也可以返回已有的 fake，不要求每次新建。
- 对“同一 fake 先正常、再超长”的回答原文：“只有input_a 原因是第一次收到input_a 跑到invoke_analyzer的时候 会向calls里append一次 然后第二次跑2001的时候 还没跑到invoke_analyzer 在check_text_length就抛异常结束了”。结论及调用顺序正确；append 的具体位置是在 invoke_analyzer 调用的 fake.analyze 内。最终 fake.calls 为 `[INPUT_A]`，既不清空旧记录，也不增加超长文本。
- 本段核心调用链已通过口头说明确认，不再追加追问。可选新增测试未要求完成，不把观察材料或口头回答当成已提交新测试；不推断其他尚未讨论的高级依赖知识已掌握。

## 学习反馈

- 今天的难度和最不清楚的一处：今天还挺简单 没有太迷糊的地方
- 实际用时（排除中断，自行填写）：20min

- 结束时间：2248
