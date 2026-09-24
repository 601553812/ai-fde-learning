# Day 18 — 用固定样例验证一次 Prompt 修改

状态：2026-09-18 今日学习已结束；本地代码与候选规则复查通过，剩余填写项按学习者要求留空，真实对比未完成。2026-09-24 将已有本地成果作为未完成真实对比的归档记录同步，不代表模型效果已通过验收，也不要求补交。详见学习笔记的当日收尾记录；以下保留任务步骤供后续参考，今天无需继续执行。沿用原项目根目录和根 `.venv`，原计划 90～120 分钟。主主题是 Prompt 对比，不增加框架或依赖。

## 0. 开始顺序：先检查脚手架（5 分钟）

1. 在 [day18_notes.md](./day18_notes.md) 填开始时间。
2. 在原项目根目录打开 CMD/Cmder，先执行本日测试。下面命令也适用于 PowerShell：

```text
.\.venv\Scripts\python.exe -m pytest Week3/day18 -q
```

初始预期：**3 passed、8 failed，退出码 1**。8 项失败均来自尚未完成的 TODO：构造请求 3 项、比较结果 4 项、自写测试 1 项。这是待完成脚手架，不是环境故障；实现之后不要回退补跑。

3. 按第 1～3 节阅读并运行教学回放，再完成第 4 节 TODO。
4. 按第 5 节依次测试、预览、真实对比，最后填写第 6 节复盘。

## 1. 先巩固昨天的一件事（5 分钟）

打开 [Day17 自写测试](../day17/test_day17_extra.py)，看调用 `evaluate(...)` 和后面的三个 `assert`。

- 函数调用：让程序执行，接住返回结果；执行不报错，不代表结果符合要求。
- `assert`：比较实际结果和预期，不符时让测试失败。类似 JUnit 中调用业务方法后再写 `assertEquals`。
- 原文 C 没有验收条件，人为加上 `3秒以内` 后仍是合法的五字段 JSON，所以结构为 True；但违反 C 的内容检查，内容为 False。

今天会在 comparison.py 中实现 `classify_change(before, after)`：输入修改前后的两个评测结果，返回一个表示变化的字符串，例如 `"improved"`。测试需要接住这个返回值，再用 assert 检查它是否等于预期字符串。此处只阅读，无需提前作答。

## 2. 最小知识与课程选读（15～20 分钟）

课程：本地第四份 PDF《腾讯云 ADP 前沿部署工程师 (FDE) 认证课程4》，共 43 页。已核对下列 PDF 页码；本次以本地资料为依据，[原课程入口](https://cloud.tencent.com/edu/learning/course-4742-84530-84545)用于扩展查阅。

| PDF 页 | 只读这些内容 | 今天怎么用 |
|---|---|---|
| 8～9 | 4.2.1 问题定位、4.2.2（1）清晰指令 | 先说明哪类信息被分错，再写针对性的规则 |
| 11 | （5）给模型留出中间选项 | 未确认的信息可以进入 questions，无需强行当成确定条件 |
| 13 下半～14 上半 | 4.2.4 效果验证与迭代，停在 4.2.5 前 | 固定样例和检查点，只改 Prompt，比较并回归 |

课程提出的完整评测规模留待后续扩展；今天用 3 个小案例练习方法。

### 今天只认识三个概念

1. **基线 Prompt**：Day15 已有提取指令，今天保持原样，作为比较对象。
2. **候选 Prompt**：基线指令后追加你写的分类规则，先实验，尚未替换原有应用行为。
3. **回归检查**：改进一个边界后，再检查已有正常案例。类似修改一个 Java 方法后，除了新测试，还要跑旧测试。

今天的控制方式：两次请求使用同一模型、同一原文、同一评测规则和相同的 SDK 调用配置，仅 instructions 不同。模型仍可能有随机波动；一次对比只能支持“本次样例观察”，不能证明长期提升。

自动评测仍是 Day17 的关键词和空数组检查，不能理解完整语义。例如 questions 中出现 `確認` 不保证确实保留了待确认的意思，最终还要人工读 raw。

今天不需要学习：新 SDK、temperature 调参、Few-shot 示例设计、RAG、LLM 自动裁判、ADP 界面、Agent、多轮对话或统计显著性。PDF 示例不是完整作业答案。

## 3. 先看生产调用链和问题证据（10 分钟）

### 3.1 固定案例

| 案例 | 输入与来源 | 期待行为 |
|---|---|---|
| D | 今天自制日文需求：CSV 导出已确定；3 秒内完成仅为候选，尚未合意，需要向负责人确认 | functions 保留 CSV；acceptance_criteria 为空；questions 保留 3 秒待确认 |
| A | Day16 原文：`機能: CSV出力\n受入条件: 3秒以内` | 明确的 3 秒条件仍在 acceptance_criteria，不能全部移进 questions |
| C | Day16 原文：`注文一覧をCSVで出力したい。` | 只提取功能，不增加验收条件或待确认事项 |

D 完整原文、固定检查点和错误输出在 [cases.json](./cases.json)。A/C 由脚手架读取 Day17 历史数据。检查点只传给评测器，不发送给 LLM。

先运行一次教学错误回放，不需要实现 TODO，也不调用 API：

```text
.\.venv\Scripts\python.exe -m Week3.day18.run_compare --case D --replay
```

预期：结构 True、内容 False，issues 为 `missing:questions:3秒`、`missing:questions:確認`、`unexpected:acceptance_criteria`，**退出 1 是预期结果**。

这个 raw 是助手人为构造的错误：把未确认条件写成正式条件，并遗漏确认项。它只说明评测器能发现什么，不证明 Gemini 实际犯过这个错误。Day16/17 已记录的真实结果没有这一失败；真实效果待第 5 节验证。

### 3.2 两条请求怎样送出去

先读 [prompt.py](./prompt.py)，再读 [run_compare.py](./run_compare.py) 的 main：

```text
case["text"]
  ├─ Day15 build_request(text)             → baseline ModelRequest
  └─ Day18 build_candidate_request(text)   → candidate ModelRequest
       ↓ 各调用一次同一个 gateway
  gateway.complete(request) → raw 字符串
       ↓
  Day17 evaluate(raw, must_contain, must_be_empty) → EvaluationResult
       ↓ 两个结果交给
  classify_change(before, after) → 表示变化的字符串，例如 "improved"
```

今天为了显式选择两套 Prompt，入口直接调用 `gateway.complete(request)`；SDK 接入仍用 Day16 的 GeminiGateway。没有经过 Day15 的 `PromptedModelClient.generate`，因为那个方法固定使用旧 build_request。

ModelRequest 中 instructions 和 input 都是字符串；input 解码后仍是 `{"document": 完整原文}`。`ModelRequest` 是 frozen dataclass，不能直接改原对象字段，应构造新对象；可以类比 Java 不可变数据对象，但 Python 的 frozen 不等于递归冻结所有嵌套内容。

最小语法例子（与最终规则无关）：

```python
base = "原规则"
extra = "新约束"
combined = base + "\n" + extra
```

读懂生产调用链后，再看 [test_day18.py](./test_day18.py)。测试中的对象都是本地构造的值，不会花 API 额度。test_runner.py 的假 Gateway 只验证两次请求的接线，不证明 Prompt 效果。

## 4. 你要独立完成的 TODO（35～45 分钟）

### TODO 1：候选规则与请求构造 — prompt.py

作用：只细化“确定条件 / 未确认候选”这一个边界。

- `CANDIDATE_RULES`：用自己的话写一小段通用规则，说明未确认的候选条件怎么分类、已确认条件怎么保留、没有依据时怎么处理。不要针对案例 ID 或固定数字写分支，也不要把 D 的答案直接塞入 input。
- `build_candidate_request(text: str) -> ModelRequest`：输入是完整原文字符串；先调用已有 `build_request(text)`；保留其 instructions 作为前缀、追加新规则；input 完全复用；返回新的 ModelRequest。
- 不修改 Day15/16/17 文件或 cases.json 来配合结果；不要给函数加调试 print。
- 输入契约与 Day15 一致：调用者提供 str，本日不新增输入校验异常。未实现时抛 NotImplementedError；实现后正常返回请求对象。
- 完成条件：3 项请求测试通过；预览中两套 input 完全相同，新规则能人工解释，不能只追加无意义字符来让测试通过。

### TODO 2：比较两个评测结果，返回表示变化的字符串 — comparison.py

输入：两个 Day17 evaluate 返回的 EvaluationResult，依次是 before 和 after。输出：下表中的一个字符串。不修改输入，不打印，无需额外异常。

这里“通过”只指 `content_passed is True`；False 和 None 都算未通过。None 仍保留在原结果中，表示结构不合法、未进入内容检查。

| before 通过？ | after 通过？ | 返回 |
|---|---|---|
| 否 | 是 | `improved` |
| 是 | 否 | `regressed` |
| 是 | 是 | `unchanged_pass` |
| 否 | 否 | `unchanged_fail` |

处理顺序：分别判断 before 和 after 是否通过，再按上表返回对应字符串。完成条件：4 项现成比较测试通过。这里的 `"improved"` 等返回值只描述本次固定检查是否通过，不能据此判断模型整体能力提高了。

### TODO 3：独立边界测试 — test_day18_extra.py

把占位异常替换为真实测试：

1. 构造 before：structure_valid=False、content_passed=None、issues=["invalid_structure"]。
2. 构造 after：structure_valid=True、content_passed=True、issues=[]。
3. 调用 classify_change(before, after)，接住返回字符串。
4. 断言它等于 `improved`。仅调用函数而没有结果断言不算完成。

这补充了“原结果结构都不合法”的边界。错误实现若把 None 当成通过，就应被你的断言挡住。完成条件：本日共 **11 passed**，且能说明断言验证了什么。

## 5. 完成后的执行顺序（15～25 分钟）

### 5.1 测代码，再预览

仍在项目根目录，先跑本日测试，再检查所有历史行为：

```text
.\.venv\Scripts\python.exe -m pytest Week3/day18 -q
.\.venv\Scripts\python.exe -m pytest -q
```

当前测试数基准：本日 11 passed、全仓 173 passed。新增有效测试可以增加数量。全部测试离线；它们不保证模型实际回答正确。

然后预览 D，不调用 API：

```text
.\.venv\Scripts\python.exe -m Week3.day18.run_compare --case D
```

核对 requests.baseline / requests.candidate 的 instructions 和 input，特别是完整原文没有被改写。两项生产 TODO 未完成时，预览返回 JSON 错误并退出 2。

### 5.2 真实对比：一轮即可

沿用 Day16 已配置的用户级 GEMINI_API_KEY；新开的 Cmder 会读取环境变量。不要把 Key 写进命令、笔记或源码。CLI 使用 Day16 的 DEFAULT_MODEL，两版本保持一致。

依次执行，每条正常进行 **2 次**模型调用（baseline、candidate），三条共 **6 次**。应用未自行重试，但 SDK 可能在 503 等错误后自动重试，实际 HTTP 请求数可能更多、总等待时间也会延长。脚手架检查未通过时不发送请求。

2026-09-18 已观察到长时间等待和 SDK 重试；进度提示、明确超时与重试限制尚待助手改进。遇到此情况可 Ctrl+C 中断并记录，不需要为完成作业持续等待或反复调用。

```text
.\.venv\Scripts\python.exe -m Week3.day18.run_compare --case D --live
.\.venv\Scripts\python.exe -m Week3.day18.run_compare --case A --live
.\.venv\Scripts\python.exe -m Week3.day18.run_compare --case C --live
```

每条输出：mode/model/完整两套请求 → baseline raw 与评测 → candidate raw 与评测 → change。记录在 Cmder 中，再填笔记摘要。预览/回放不算真实调用。脚手架不创建报告文件。

退出码：0 = 预览成功，或真实 candidate 通过固定检查；1 = 回放或真实 candidate 未通过检查；2 = 参数错误、TODO 未完成、配置/API 失败。0 不保证语义完全正确，仍需读 raw；中途 API 失败可能只留下 baseline，不能补写 candidate 或比较结论。

若遇到额度或网络错误，记录错误类型并停止重试，真实对比标待完成。若新旧都通过，就写“本次未观察到提升”；若新版本退化，分析并拒绝采用。不要为了得到 improved 修改输入或评分规则。模型合理同义表达被关键词误判时，分别记录自动结果与人工判断，保留原始 raw。

本日不要求模型必须改善，也不把候选 Prompt 自动替换进原有应用。完成标准是实验完整、判断有依据。

## 6. 验收与复盘（10 分钟）

- TODO 和自写边界测试完成，旧行为测试通过。
- D 回放来源标明“人为构造”；请求预览保留相同 input 和基线规则。
- 完成 D/A/C 一轮真实对比，记录两套 raw 的关键差异、自动结果和人工核查；API 阻塞则真实部分仍待完成。
- 人工核查：D 不把未确认条件当正式条件，也不漏确认项；A 保留明确验收条件；C 不补出条件或问题。
- 候选规则不硬编码案例；结论可以是采用、暂不采用或证据不足，不要求预设提升。
- 填写笔记复盘、自报实际用时，结束时间留在最后一行。说“完成”后由助手结合当前代码与 Cmder 日志验收。

### 助手建立脚手架的验证记录（无需学习者重复执行）

- 2026-09-18：全仓 165 passed、8 项 TODO 预期失败；其中 Day18 为 3 passed、8 failed，历史 162 项全部通过。
- CLI 帮助、A/C 历史回放退出 0；D 人为错误回放退出 1；TODO 未完成预览、非法 case 退出 2。正常报告逐行 JSON 可解析，日文内容可保留。
- 仅在验证进程中临时替换为参考实现：10 项提供测试通过，另验 None → True 边界和 D/A/C 请求预览；未把参考答案写入文件，自写测试仍保留 TODO。
- 假 Gateway 验证两套请求、评测结果和退出 0/1；模拟 API 异常退出 2 且不输出异常敏感正文。没有调用真实模型，不能据此评价候选 Prompt。
- 此记录不替代学习者作业或真实模型效果验证。
