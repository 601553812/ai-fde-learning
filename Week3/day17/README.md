# Day 17 — 建立需求提取的小型评测基线

状态：2026-09-17 已完成；自写测试断言和 JSON 报告已修正，全仓 162 passed。自报实际用时 1.5h。以下保留学习步骤，供回顾使用。

## 0. 开始顺序与脚手架状态

1. 在 day17_notes.md 填开始时间，确认终端位于项目根目录。
2. 若首次拿到未实现脚手架，先执行下面的本日测试，再进入第 1～3 节讲解。命令适用于 CMD/Cmder 和 PowerShell：

```text
.\.venv\Scripts\python.exe -m pytest Week3/day17 -q
```

初始脚手架预期 10 failed：9 项提供测试调用尚未实现的函数，1 项自写测试仍为占位；均因 TODO 的 NotImplementedError 失败，pytest 退出 1。这是初始状态，不是环境故障。已经实现后应为 10 passed，不需要还原代码补跑失败状态。

3. 阅读第 1～3 节后完成第 4 节 TODO；实现中可重跑本日测试。完成后按第 5～6 节运行回放与验收。

本节按学习者反馈补齐执行顺序；Day17 当时未明确要求先跑初始脚手架，不将未运行计为漏交。末尾“脚手架验证”是助手建立材料时的历史记录。

## 1. 先从昨天的一行继续（5 分钟）

在 [Day16 真实入口](../day16/real_call.py) 中，你已经理解：

```python
raw = client.generate(case["text"])       # 模型回答的字符串
requirements = decode_requirements(raw)  # 解析、校验成 RequirementData
```

今天的问题：C 原文只写了导出 CSV。如果模型返回合法 JSON，却增加 `acceptance_criteria=["3秒以内"]`，第二行仍可能通过。我们需要为 C 预先写下“验收条件必须为空”，再用代码检查实际回答。

注意先前讲解中的简化：真实 SDK 的 `system_instruction` 是完整规则字符串，`input` 也是字符串；为了讲解而把规则改画成对象的示意图不是实际请求格式。今天的评分规则 `must_contain`、`must_be_empty` 只交给评测器，不发送给模型。

## 2. 课程选读与最小知识（20 分钟）

本地 `腾讯FDE教程/腾讯云 ADP 前沿部署工程师 (FDE) 认证课程4 - 腾讯云培训认证.pdf`，共 43 页。已核对以下 PDF 页的文字；只选相关段落：

| PDF 页 | 范围 | 今天对应的动作 |
|---|---|---|
| 1～2 | 4.1.1 单次调试与批量评测；第 2 页五步法 | 把昨天单次结果整理成可重复检查的样本 |
| 3～4 | 4.1.3 开头及第 4 页触发条件表，停在“评测任务”前 | 固定输入和检查点，后续改 Prompt 时用同一批样例 |
| 5 | 只读“规则打分”和“代码打分”两小段 | 自己写 Python 检查已声明条件 |

这里借用课程评测方法；三条样例只是教学基线，不能代表大规模评测或上线依据。不做 ADP 界面操作，不要求完成互动或视频。原资料入口见 [课程页](https://cloud.tencent.com/edu/learning/course-4742-84530-84545)，本次以本地 PDF 为依据。

### 三个名字

- 评测集：固定的一组“输入、检查点”。当前用 A/B/C。
- 基线：以后拿来比较的已记录结果。`baseline.json` 的 raw 来自 Day16 笔记，不是今天重新生成的输出。
- 评测器：对结果打标记的普通 Python 函数。今天不让另一个 LLM 打分。

例如 A 的检查配置是：

```json
{
  "must_contain": {"functions": ["CSV"], "acceptance_criteria": ["3秒以内"]},
  "must_be_empty": ["risks", "questions", "unknown"]
}
```

`must_contain` 的 key 是要检查的分类；value 是这个分类必须包含的所有关键词。一个关键词只要在该分类的任意一条字符串中出现就满足。`must_be_empty` 列出的分类必须为 `[]`。

### 只用已学语法，加一个小例子

```python
data = requirements.model_dump()  # RequirementData → dict
items = ["検索画面を追加する", "検索結果を保存する"]
found = any("保存" in item for item in items)
# found 为 True：至少一项包含“保存”
```

`"保存" in item` 检查子串；`any(...)` 表示至少一个条件成立。也可用普通 for 循环实现，不强制用推导式。不要用 `"CSV" in ["CSV出力"]`，那检查的是列表中有没有完全等于 `"CSV"` 的元素。

Java 对照：`item.contains(keyword)` 对应子串检查；`stream().anyMatch(...)` 对应 `any(...)`。Python `in` 会随容器类型改变含义，不能当成 Java 的同一个方法。

输出 `EvaluationResult` 是已提供的 dataclass，类似只装数据的 Java DTO；不是 AI 模型。`content_passed=None` 表示结构不合法，未进行内容评分；`False` 表示已评分且发现问题。序列化为 JSON 时 `None` 显示为 `null`。

### 这些规则的边界

关键词规则无法理解所有同义词、否定或矛盾。例如“CSV出力は不要”也包含 CSV，可能误通过。B 的关键词检查也不能自动发现所有擅自决定编码的问题；仍需人工核查。不要将报告里的 `content_passed` 写成“事实一定正确”。

## 3. 先看非测试调用链（10 分钟）

按 `baseline.json` → `evaluation.py` → `run_eval.py` 的顺序看，再读测试：

```text
run_eval：读取 baseline.json 的一个 case
  → 取 raw 和该案例检查点
  → evaluate(raw, must_contain, must_be_empty)       [TODO 2]
      → decode_requirements(raw)                  [Day14 已完成]
      → check_content(requirements, ...)          [TODO 1]
      → 返回 EvaluationResult
  → 打印单条结果和汇总
```

默认回放没有 `client.generate()`；只有 `--live --case C` 才调用 Day16 Gateway，拿新 raw 走同一个评测器。评分标准由本地文件读取，生成新回答时不会发给模型。

## 4. 独立实现（45～60 分钟）

只修改 `evaluation.py` 和 `test_day17_extra.py`。本地检查配置视为可信：字段名属于已知五分类，关键词非空字符串；今天不用新增配置校验库。

### TODO 1：check_content

输入：已经通过结构校验的 `RequirementData`、`must_contain` 字典、`must_be_empty` 列表。输出：全部失败原因组成的 `list[str]`；不修改输入，不发网络请求，不写文件。

处理步骤：

1. 用 `model_dump()` 取得字典。
2. 按 `must_contain` 的字典顺序和关键词列表顺序检查。每个关键词在指定分类的任意一项里出现就通过；不能去别的分类找，也不能把多项拼接后凑成关键词。
3. 找不到时追加 `missing:<字段>:<关键词>`，如 `missing:risks:文字化け`。
4. 再按 `must_be_empty` 列表顺序检查，不为空时追加 `unexpected:<字段>`，如 `unexpected:acceptance_criteria`。
5. 返回所有问题；没有问题返回 `[]`。不能发现第一项问题后就提前返回。

验证：提供测试检查 B 漏掉风险、关键词落入错误分类、多项不能拼接，以及无检查项时返回空列表。

### TODO 2：evaluate

输入：raw 字符串和上述两个检查配置。返回 `EvaluationResult`：

| 情况 | structure_valid | content_passed | issues |
|---|---|---|---|
| decode_requirements 抛 InvalidModelOutput | False | None | `["invalid_structure"]` |
| 结构合法，check_content 返回空列表 | True | True | `[]` |
| 结构合法，发现内容问题 | True | False | check_content 返回的完整问题列表 |

先调用 `decode_requirements`；只捕获 `InvalidModelOutput` 并返回结构失败结果，不执行内容评分。成功时调用 TODO 1 并据结果构造返回对象。不要捕获所有 Exception 来掩盖代码写错；不要把“解析成功”当成“内容通过”。

### TODO 3：自写 C 编造验收条件的测试

在 `test_day17_extra.py` 中替换占位：用 `load_baseline()` 取得 C；`json.loads(c["raw"])` 得到 dict，把 `acceptance_criteria` 改成 `["3秒以内"]`；`json.dumps()` 转回 raw；调用 `evaluate`，传入 C 原有检查点。

断言 `structure_valid is True`、`content_passed is False`，且 `issues == ["unexpected:acceptance_criteria"]`。这份错误输出是人为构造的测试数据，不能记录成 Gemini 实际编造。

## 5. 运行与观察（15 分钟）

以下从项目根目录运行，CMD/Cmder 和 PowerShell 通用。使用现有根 `.venv`，无新增依赖。

```text
.\.venv\Scripts\python.exe -m pytest Week3/day17 -q
.\.venv\Scripts\python.exe -m Week3.day17.run_eval
.\.venv\Scripts\python.exe -m Week3.day17.run_eval --case C
```

本节在实现后执行，本日测试应为 10 passed。离线回放应显示 `mode=replay`，A/B/C 均为结构通过、内容检查通过，汇总 `total=3, structure_valid=3, content_passed=3`。这只是历史输出在当前规则下的结果；未完成 TODO 就运行回放会提示 TODO、退出 2。

完成离线测试后，可选用一次 C 真实调用观察新结果（会消耗账号额度；不需要重新设置 Key）：

```text
.\.venv\Scripts\python.exe -m Week3.day17.run_eval --live --case C
```

本日必做是历史基线和错误样例检测；真实调用是可选观察，不将回放描述为新模型结果。live 中 API/网络错误只打印错误类型，避免输出完整 SDK 异常；它们不能记成内容评分失败。

入口由助手提供，无需实现：帮助退出 0；全部检查通过退出 0；结构或内容不通过退出 1；非法参数、TODO、live 配置或调用失败退出 2。`--live` 必须指定单个 case。程序只打印 JSON 报告，不保存文件。CMD 用 `echo %ERRORLEVEL%`，PowerShell 用 `$LASTEXITCODE` 查看退出码。

## 6. 验收与复盘（10～15 分钟）

- 本日所有测试通过，自写测试确实构造 C 的无依据验收条件。
- A/B/C 历史 raw 与 Day16 记录一致；回放汇总正确，报告保留问题列表。
- 非 JSON、漏风险、编造验收条件分别被标为对应错误；坏结构的内容评分是 None。
- 历史测试继续通过，CLI 帮助/参数/返回码、UTF-8 和无输出文件行为符合说明。
- 在 `day17_notes.md` 填结果、两题复盘及自报用时；结束时间留在末行。可选 live 未运行就写未运行。

今天不需要：新 SDK、自动 Prompt 搜索、LLM 裁判、多模型比较、RAG、Agent、统计显著性、完整评测平台。下一步再依据失败样例进入课程 4.2 的 Prompt 调优。

## 脚手架验证（历史：助手，2026-09-17 建立时）

- 实际工作区：历史 152 项通过，本日 10 项预期失败，均由 TODO 占位导致。
- 在独立验证进程中使用未写入作业的参考实现：9 项提供测试、C 编造边界、报告汇总、CLI 0/1/2、UTF-8、无报告文件生成均通过。
- 建立时 baseline 的三条原文和 raw 已分别核对 Day16 cases.json 与笔记；当时未做新真实调用、本日未完成。最终状态见开头及本日笔记。
