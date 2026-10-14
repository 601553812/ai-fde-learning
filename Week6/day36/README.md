# Day36 — 记录并汇总人工依据核查

状态：已完成（2026-10-15最终验收）。唯一主题：**把人对照原文后的判断保存为记录，再汇总通过与需改进的案例**。参考 90～120 分钟；实际用时自报1h、难度中。下方TODO、初始失败与中途待补描述为原作业契约和历史过程，当前结论见第10节。

代码与 105 项已通过测试复制自 Day35，导入、monkeypatch 路径和入口日名更新为 `Week6.day36`。保留切块、关键词检索、上下文预算、问答、编号检查、资料定位及 HTTP 适配行为；历史代码不修改。只需学习下面的新模块，复制的其他模块不用重学。无新依赖，演示离线零调用。

## 1. 按这个顺序开始

工作目录：仓库根目录。以下单行命令适用于 **PowerShell 与 CMD/Cmder**，使用根 `.venv` 的 Python 3.11。

1. 在 [学习记录](./day36_notes.md) 填开始时间，无需提前回答概念题。
2. 运行一次初始脚手架检查，然后读第 2～3 节。

```text
.\.venv\Scripts\python.exe -m pytest Week6/day36/tests -q
```

初始预期 **105 passed / 23 failed**，退出 1。旧行为通过，新失败来自两个函数与独立测试的 TODO 占位；是作业起点。实现后不用还原占位。

3. 先读非测试代码：`code/review_cases.py` 中的四例 → `code/qa_review.py` 的两类数据 → 两个 TODO 的签名 → `code/run_review_demo.py` 的调用顺序。
4. 按第 4～6 节只修改两个文件，测试、演示、再填写复盘和实际用时。

## 2. 先复习一次，再明确今天由谁判断

昨天的 `first.chunk_index=7`、`second.chunk_index=3`，按 first、second 顺序发送。回答的 `[2]` 指 **context.chunks[1]，也就是 second**；chunk_index=3 是它在原文档内的位置。这次只回看，不补旧题。

今天使用同一份原文：

```text
[1] returns_faq.txt (0:28)
返品期限は30日です。
開封済みの商品は返品できません。
```

先对照“问题问什么、回答说什么、这份实际发送的资料写什么”，人再选择下面四种 `verdict` 字符串。这里 verdict 就是**人填写的核查结论**，不是新的模型状态。

| verdict | 具体判定条件 | 本日例子 | 计入通过？ |
|---|---|---|---|
| `supported` | 回答回答了问题，关键事实由已发送资料支持 | 问期限，回答30日 | 是 |
| `unsupported` | 给出事实回答，但关键事实与资料冲突或没有依据 | 问期限，回答90日 | 否 |
| `correct_refusal` | 拒答，而已发送资料确实没有问题所需信息 | 问送料由谁承担，资料没有写 | 是 |
| `incorrect_refusal` | 拒答，但已发送资料已经给出问题的答案 | 问期限，资料明写30日仍拒答 | 否 |

A/B 沿用 Day34 的公开原回答；wrong_90、wrong_refusal 是示意反例。四例的人工结论和理由由助手预先给出，供演示工程行为，不算你独立核查，也不冒充四次真实模型结果。今天在笔记中用这四例对照原文，不增加真实调用。

**编号信息与人工结论分开保存：** B 和 wrong_refusal 的原回答文字相同，编号检查都为 `["missing_citation"]`，但问题不同，因此人工结论不同。wrong_90 的编号检查为 `[]`，仍是 unsupported。不要根据编号检查列表自动选 verdict。

`generated` 只表示问答流程已有回答文字。本日只记录 `status="generated"` 的待审回答；`no_context` 是应用未调用模型的路径，今天明确拒绝把它计为模型拒答案例。人工判断的范围是本次已发送资料，不是整个知识库是否包含答案。

## 3. 最小知识与普通调用链

没有新库。复用 dataclass、list、dict、for、if、ValueError、`asdict()`。今天额外用字典给四种 verdict 计数，以及 `None` 表示空报告的比例尚无意义。

与作业不同的最小例子：

```python
# 字典用字符串作键；类似 Java Map<String, Integer>，但 Python 不需要装箱语法。
counts = {"apple": 0, "orange": 0}
fruit = "apple"
counts[fruit] += 1  # 先读该键的当前计数，再加一并写回；当前 apple 为1。

number_of_items = 0
ratio = None  # 没有样本时不做除法；不同于“有样本且全部失败”的0.0。
```

Chrome 已核对 [Python 3.11 官方字典基础](https://docs.python.org/3.11/tutorial/datastructures.html#dictionaries)：只需知道字符串键、读写值和 `in`；不必通读该章。`dict[str, int]` 是类型标注，不会自动创建四个键或累计数字，和 Java 泛型有相似目的，但 Python 不会仅因标注而在运行时验证所有元素。

`ReviewRecord` 保存一例的人工结论、理由、同一个 QAResult，以及自动编号检查和原片段。`ReviewSummary` 保存总数和四类计数。`@dataclass(frozen=True)` 阻止重新赋值字段，**不冻结字段内部的 list/dict**；所以每次汇总都要返回自己的新计数字典，不共用上次的字典。这一点复用已讲过的对象与容器区别。

```text
run_review_demo.main()
  → demo_review_inputs()：取得四条已提供的人工核查示例
  → 每例调用 make_review_record(..., verdict, reason)
      → 校验输入
      → 用已有 review_qa_result()、find_cited_chunks() 取得编号信息与原文
      → 返回 ReviewRecord
  → summarize_reviews(records)：按人填写的 verdict 汇总
  → asdict + json.dumps：打印一份完整报告
```

测试直接调用这两个普通函数，无网络依赖需要替换。比例只描述传入的已核查记录；四个示例里通过2个得到0.5，**不能称为模型在真实用户问题上的准确率**。数据包含反例，样本又少。

今天不学自动事实评分、LLM-as-judge、Embedding/向量库、Prompt 改善、数据库持久化、Web 界面、并发或 Docker；不新增腾讯课程读书报告。课程只对应路线“4.1 评测基础”的调用成功与内容正确区别，必要概念已在本节讲清，不要求额外选读整份材料。

## 4. TODO 1：保存一条人工核查记录

修改 `code/qa_review.py` 的 `make_review_record(case_id, question, result, verdict, reason)`。

- 目的：使每条人工判断可以回查原问题、原回答、原资料，保留已有编号信息。
- 输入：字符串 case_id/question/verdict/reason，以及 QAResult。类型按签名传入；不额外处理 None、数字等错误类型。
- 输出：新的 `ReviewRecord`，包含签名提供的五项，以及 `citation_errors`、`cited_chunks`。
- 校验必须按下表从上到下进行；首次失败抛 `ValueError`，**完整消息**须与表一致，不包含原输入。不做其他语义校验。

| 顺序 | 无效条件 | 完整错误消息 |
|---|---|---|
| 1 | case_id 为空或全空白 | `invalid_case_id` |
| 2 | question 为空或全空白 | `invalid_question` |
| 3 | result.status 不等于 generated | `unreviewable_status` |
| 4 | verdict 不在 VERDICTS，严格区分大小写、不清理空白 | `invalid_verdict` |
| 5 | reason 为空或全空白 | `invalid_review_reason` |

- 合法 case_id/question/reason 原样保存，包括首尾空白；strip 只用于判断空白，不用其结果替换原文字。
- `record.result is result` 必须成立；不能重建问答结果、改 status/answer/context、修改片段内容或顺序。
- `citation_errors` 使用已提供的 `review_qa_result(result)`；`cited_chunks` 使用已提供的 `find_cited_chunks(result.answer, result.context)`，返回新列表、里面是原片段对象。
- verdict/reason 来自调用方，原样保存。函数不自行理解日文、不从引用错误反推结论，不重新请求模型、不读取或写入文件。
- 处理步骤：依次校验五项 → 取得两项编号/原文信息 → 组装并返回记录。

已有导入可直接使用，不需要配置 `__init__.py`。只做本 TODO 时，全日目标 **119 passed / 9 failed**；剩余为汇总及独立测试（含演示依赖汇总）。

```text
.\.venv\Scripts\python.exe -m pytest Week6/day36/tests/test_qa_review.py -k "not summary and not demo" -q
```

## 5. TODO 2：汇总已核查记录，处理空输入

修改同文件 `summarize_reviews(records)`。

- 目的：让同一份报告看见每类问题与通过比例，空报告不伪装成失败或成功。
- 输入：`list[ReviewRecord]`，每项符合 TODO 1 的合法记录契约；本函数不重复验证字段。每项是一次核查记录，即使 case_id 相同也逐项计数，本日不做去重。
- 输出：新的 `ReviewSummary`；不新增异常。

| 字段 | 要求 |
|---|---|
| total | 输入记录条数 |
| verdict_counts | 四种 VERDICTS 键都存在，未出现也保留0；每条记录为自己的 verdict 加1 |
| passed | supported 与 correct_refusal 的数量之和 |
| failed | unsupported 与 incorrect_refusal 的数量之和；也应等于 total - passed |
| pass_rate | total > 0 时为 passed / total，不乘100、不四舍五入；空输入为 None |

- 每次调用创建新的计数字典，不使用模块级累计状态，不修改或排序 records，也不改任何 record/result/列表内容。
- 处理步骤：建立本次四类零计数 → 遍历记录计数 → 计算总数/通过数/未通过数 → 根据总数计算比例或 None → 返回汇总。
- 边界功能由你实现：空输入返回 total/passed/failed 都为0，四类计数都为0，pass_rate=None；连续调用不能沿用上次结果。

TODO 1～2 完成后，全日目标 **127 passed / 1 failed**，仅剩独立测试占位。

```text
.\.venv\Scripts\python.exe -m pytest Week6/day36/tests/test_qa_review.py -q
```

## 6. TODO 3：独立验证合理拒答计入通过与连续调用

修改 `tests/test_day36_extra.py` 中已命名的测试。使用这些具体子模块导入：

```python
from dataclasses import asdict  # 把数据类转为字典便于比较完整结果。
from Week6.day36.code.qa_review import make_review_record, summarize_reviews
from Week6.day36.code.review_cases import demo_review_inputs
```

无需改 `code/__init__.py`；以上导入类/函数所在的模块，不是包导出，也不导入历史日。删除 pytest.fail 占位；无网络替身或文件操作。

输入与操作顺序：

1. 调用 `demo_review_inputs()`，取 B（下标1）和 wrong_90（下标2）。它们的 question/result/verdict/reason 已提供；各调用一次 make_review_record 建成两条记录。
2. `records` 按 B、wrong_90 顺序保存；调用汇总前保存完整数据快照和这两条原对象。
3. 第一次 `summarize_reviews(records)`。
4. 第二次 `summarize_reviews([])`。
5. 第三次 `summarize_reviews([wrong_90 的那条记录])`。

三次输入均合法，应正常返回。断言三次**完整**汇总（用 asdict 比较可行），值如下；不是只断言两三个字段：

| 字段 | 第一次 | 第二次 | 第三次 |
|---|---|---|---|
| total | 2 | 0 | 1 |
| passed | 1 | 0 | 0 |
| failed | 1 | 0 | 1 |
| pass_rate | 0.5 | None | 0.0 |
| supported 计数 | 0 | 0 | 0 |
| unsupported 计数 | 1 | 0 | 1 |
| correct_refusal 计数 | 1 | 0 | 0 |
| incorrect_refusal 计数 | 0 | 0 | 0 |

四类计数是每份汇总的 `verdict_counts` 字典。额外断言三次结束后：输入 records 的完整数据和顺序未变，两个位置仍分别 `is` 原 B 记录、原 wrong_90 记录；三份 verdict_counts 两两不是同一个字典（`is not`）。第一次汇总不应被后两次改写，最后再次检查其完整结果。

这能发现把 missing_citation 当失败、空输入除零、沿用上次计数或共用字典等不符合契约的行为；断言失败本身不自动诊断根因。完成目标全日 **128 passed，无警告**。

## 7. 演示、人工对照与最后验收

```text
.\.venv\Scripts\python.exe -m pytest Week6/day36/tests -q
.\.venv\Scripts\python.exe -m Week6.day36.code.run_review_demo --help
.\.venv\Scripts\python.exe -m Week6.day36.code.run_review_demo
```

- 测试与 help 退出0；正常演示退出0，打印一行完整 UTF-8 JSON：四条 reviews、一份 summary、gateway_calls=0。不生成文件，不需要密钥。
- summary：total=4、passed=2、failed=2、pass_rate=0.5，四类计数各为1。
- 原回答来源 A/B 为 recorded_day34，两反例为 synthetic；全部 review_origin 为 provided_manual_example，说明人工结论已提供。
- 对照 B 的 question 与 wrong_refusal 的 question，以及各自资料，说明为何同一句拒答得到不同判定；检查 wrong_90 有合法编号仍未通过。
- 任一函数未实现时入口打印 TODO 提示、退出1，无 traceback；非法参数由 argparse 退出2。以上退出码不代表内容效果分数。

在笔记填写三题复盘、自报实际用时、难度与仍需讲解位置，再做本日验收。128项测试通过只证明保存/汇总等工程行为，不替代真实模型质量证据。完成并验收后按项目规则提交推送；本次只建立学习材料，不标记完成。

## 8. 助手建立验证（非学习者必做）

- 新增练习前，本日复制行为 105 passed；Python 3.11.15、pip check通过。
- 初始占位实测105 passed / 23 failed，无警告；仅在临时进程替换函数和独立测试后128 passed，无警告，参考答案未写入作业。
- 实际占位入口help/未实现/非法参数退出0/1/2；临时参考的正常演示返回0，完整UTF-8 JSON、资料位置、四类汇总、零调用与无输出文件验证通过。详情见学习记录，不作为学习者完成证据。
- 新周全仓回归1483 passed / 23项本日预期TODO失败，含此前的两条依赖弃用警告；历史1378项全部通过。UTF-8、本地链接、当天导入、敏感模式扫描与差异空白检查通过。
- Week5目录已归档，不移动历史文件。新周建立的全仓回归由助手执行，不增加学习者的历史重跑要求。

## 9. 中途检查（2026-10-15；历史过程，已解决）

- 两个核心函数符合原契约，128 passed，无警告，pip check通过；校验顺序/精确消息、原文字与QAResult保留、四类计数、正确拒答计入通过、空输入None和每次新建字典均正确。原计数不递增问题已经由学习者修正，不再作为当前问题。
- 实际子进程help/正常/非法参数退出0/0/2，一行完整UTF-8 JSON、四例来源与人工结论来源、四类各1、总数4/通过2/未通过2/比例0.5、零调用、无traceback与输出文件均通过；没有新增真实模型请求或读取终端日志。
- 独立测试已经在三次调用后比较三份完整汇总，因此第一份结果也已在后两次调用结束后核对，无需重复同一断言。还需按第6节既有要求，在调用前保存完整输入快照，结束后检查数据/顺序及两个原记录对象身份，并检查三份verdict_counts两两is not；测试通过数不能代替缺失的独立验证。
- 复盘原答与反馈已填写，助手补准见学习记录。实际用时自报1h、难度中、仍需讲解无；独立测试收尾前不标记本日完成，不提交推送。

## 10. 最终验收（2026-10-15）

- 学习者完成两个核心函数和独立测试；完整数据快照位于第一次汇总之前，三次之后检查完整数据/顺序、两个原记录对象身份、三份计数字典的全部三对身份，以及三份完整汇总。此前比较数据形式不一致、浅拷贝不足与链式比较漏首尾均已解决。
- 本日128 passed，无警告；助手新周全仓回归1506 passed，含两条此前依赖弃用警告，不作为本日问题。pip check通过；实际入口help/正常/非法参数退出0/0/2，UTF-8完整JSON、原回答/原文/结论来源、四类各1、总数4/通过2/未通过2/比例0.5、零调用与无文件/traceback均通过。
- 复盘原答、自报1h、中等难度和助手补准保留在笔记。原文对照由助手完成并标明来源；不冒充独立核查或真实模型准确率证据，不要求重写已解释过的回答。没有读取终端日志、没有新增模型请求。
- 助手只补中文块注释、清理未使用导入并整理状态，核心逻辑和独立断言由学习者完成。下次先用一个现有案例回看完整快照与对象身份，再沿固定问题/期望证据/逐例核查的评测集主线继续，不补交旧题。按默认规则提交并同步GitHub，上传以实际远端核对为准。
