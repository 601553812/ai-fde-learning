# Day 15 学习记录

## 学习开始

- 开始时间：1829
- 环境确认：根 .venv / Python 3.11；本地 RecordingGateway，无网络和费用。

## 本日学习目标（无需提前作答）

- 分清固定规则、文档原文、内部 ModelRequest 和模型返回的 raw。
- 组装请求后仍复用 Day 14 的输出校验。
- 验证特殊字符与连续请求不会改变原文或覆盖前一次数据。

## 学习后复盘

1. 验证点：请求和输出的位置。看 test_generate_returns_raw_text_and_sends_one_complete_request：INPUT_A 传入 generate，RecordingGateway 返回 not-json。请用三行写出 build_request 返回什么类型、generate 返回什么值、如果再经 ModelOutputAnalyzer.analyze 会在哪个函数拒绝该值。

答：ModelRequest
str
decode_requirements

2. 验证点：原文保留。看自己完成的最后一个测试，顺序为 INPUT_A → INPUT_B。假如 build_request 对 text 调用 strip()，第二份 input 解码后的 document 与 INPUT_B 是否相等？指出哪一处具体字符变化会导致断言失败。无需推断模型如何作答。

答：不相等
第一个字符就会出问题 因为input_b的第一个字符是空格 如果调用strip就会把空格消除

3. 验证点：验证范围。本日 12 项测试和提示词六点人工审阅都通过后，是否可以宣称“真实模型能正确提取需求”？一句话写结论，再一句话写还缺哪种证据。

答：不能 因为还没接入真实模型

## 验收记录（学习后填写）

- TODO 1 规则六点人工审阅：通过，包含资料与规则分离、只返回 JSON、五个字符串数组字段、缺项不编造、保留语言和限制外层字段。
- 自动测试：2026-09-15 助手验收全仓 151 passed，包含本日 12 项；pip check 通过。两条既有间接依赖弃用警告不影响结果。
- demo 验收：帮助/正常/坏模型输出/未知参数退出码分别为 0/0/1/2；正常输入包装和完整 AnalysisOutput 正确、日文可读；坏输出固定错误及一次调用；均无 traceback，独立临时目录无输出文件。
- 真实模型集成：未进行，供应商/模型/API 账号待确认。

## 错题本

### 1. JSON 编码与解码方向（日志证实，学习者已修正）

错误写法：

```python
document = json.loads(text)
document = json.loads(text, data={"document": text})
```

正确写法（当前实现）：

```python
data = {"document": text}
document_str = json.dumps(data, ensure_ascii=False)
```

原因：text 是需求原文，不是 JSON 文本。第一种写法出现 JSONDecodeError，表示在起始位置无法按 JSON 读取；第二种出现 TypeError，因为 JSON 解码器没有 data 这个参数。本任务要把字典编码成 JSON，因此使用 dumps；测试检查 request.input 时才用 loads 转回字典。

最小示例：`json.loads(json.dumps({"document": "検索"})) == {"document": "検索"}`。

## 复盘反馈（助手补充，原答保留）

- 第 1 题：ModelRequest 和 decode_requirements 两处正确。原答 str 是类型；题目要求的具体返回值是 `"not-json"`。此处补准“类型”和“值”的表达，不要求重抄答案。
- 第 2 题：判断正确。INPUT_B 首尾的空格会被 strip 删除，因此与原文不再相等。
- 第 3 题：结论正确，本地替身不能证明真实模型提取正确。还缺的是用真实模型处理代表性需求，并逐条对照原文检查结果的证据；这是助手补充，不记录为学习者已经独立完成的评测。

## 学习过程与贡献记录（2026-09-15）

- 学习者在原项目完成规则、两个函数及最后一项边界测试；助手检查时功能实现已正确，无需代写或修复。过程中助手提供了字典构造和解码断言示例，因此不把相应语法全记为无提示独立完成。
- Cmder 当日相关日志可见 7 轮完整 pytest 结果：3 passed/9 failed → 3 passed/9 failed → 11 passed/1 failed → 11 passed/1 failed → 11 passed/1 failed → 12 passed → Day 14～15 合并 28 passed。前五轮后续 CMD_META 的 previous_exit 为 1，最后两轮为 0；只统计完整结果，不推断全部学习尝试次数。
- 前两轮分别出现 JSONDecodeError 和不支持 data 参数的 TypeError，后续三轮唯一失败 case 为最后的连续请求测试。未据日志输出推断每一轮编辑动作或学习者的思考。
- 日志还确认 demo 帮助、正常模式和坏输出模式的退出码为 0/0/1，与助手独立验证一致。坏输出的 1 是预期业务结果，不是待修故障。
- 对话已解释 INPUT_B 当前引用、ModelRequest.input 与原文的关系、document 键、JSON 编解码。此前助手把“完成 TODO 后的流程”说成仿佛已有调用，已在对话更正，不归入学习者错误。
- 自报用时保留为 1h 多一点，难度与内容量合适，暂无线下仍需讲解项；不以开始 1829、结束 1942 或日志跨度推算用时。

## 学习反馈

- 难度与内容量：合适
- 仍需讲解的位置：无
- 实际用时（排除中断，自行填写）：
1h多一点
- 结束时间：1942
