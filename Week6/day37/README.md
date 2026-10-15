# Day37 — 固定问题集与期望证据检查

状态：已完成学习与代码验收（2026-10-16）；复盘原答与助手补准分别保留，评测对象的表述下次短复习。唯一主题：**先固定问题和期望原文，再检查准备发送的资料有没有这处证据**。实际用时自报“1h-”、难度简单。下方TODO与初始失败是原作业契约和历史过程，当前结论见第9节。

已复制Day36必要Python代码和128项测试到本日，更新导入与monkeypatch路径为`Week6.day37`。复制后128 passed；保留切块、检索、上下文、问答、编号检查、人工核查和HTTP适配行为。历史目录不改，不需重学复制模块。无新库，今天不运行真实模型入口。

## 1. 开始顺序

工作目录为仓库根目录；下列单行命令适用于**PowerShell和CMD/Cmder**，使用根`.venv`的Python3.11。

1. 在[学习记录](./day37_notes.md)填写开始时间，不必提前回答概念题。
2. 运行初始脚手架检查，再读第2～3节。

```text
.\.venv\Scripts\python.exe -m pytest Week6/day37/tests -q
```

初始实测**129 passed / 17 failed**，退出1。旧128项与数据集检查通过，其余失败来自两个新函数和独立测试的TODO占位。这是作业起点，不是历史功能故障；实现后不需还原初始状态。

3. 先读非测试代码：`code/eval_cases.py`的三份资料与六个问题 → `code/retrieval_eval.py`的数据类和签名 → `code/run_eval_demo.py`的普通调用顺序。
4. 按第4～6节实现；只需修改`code/retrieval_eval.py`和`tests/test_day37_extra.py`，再测试、演示、填写复盘。

## 2. 一例短复习与今天要解决的问题

Day36的`records.copy()`只建立新的外层列表，内部仍是原记录对象。调用前的`[asdict(record) for record in records]`保留完整数据快照；调用后与快照比较检查值是否改变，`records[0] is original`另检查原对象是否保留。这次只回看，不补交旧题。

昨天是**人对照问题、回答、已发送原文，填写verdict**。今天先检查生成之前的一步：系统准备发送的资料里，有没有预先指定的证据？

例如固定问题`返品 期限`，人工事先写下：

```text
expected_evidence.source_name = "returns_faq.txt"
expected_evidence.quote = "返品期限は30日です。"
```

检索后，`build_context()`还会按字符预算筛掉放不下的片段。即使检索命中了正确原文，预算后也可能没有发送它。因此检查对象是**context.chunks（准备发送的原片段）**，不是全部文档，也不是预算前的hits。

本日每例最多一处期望证据，匹配条件是：**同一个已发送片段的source_name完全相等，并且text含完整quote**。不是只看文件名，也不把另一文件的同一句当命中；不拼接不同片段后凑条件。匹配区分大小写，保留标点，不做strip或语义相似判断。这是这个小练习的确定规则，不是通用事实评分方法。

## 3. 六个固定问题与最小知识

所有资料和预期由助手提供、自制可公开；先固定再运行，不是六次模型回答。今天不额外要求编20题。后续沿同一格式逐步扩大评测集。

| ID | question（也是现有检索输入） | 人工预期 | 默认预算后的evidence_found |
|---|---|---|---|
| R1 | 返品 期限 | returns_faq.txt的「返品期限は30日です。」 | True |
| R2 | 開封 返品 | returns_faq.txt的「開封済みの商品は返品できません。」 | True |
| R3 | 配送 日数 | delivery_guide.txt的「配送日数は3日です。」 | True |
| R4 | パスワードを変更するには？ | account_help.txt的「パスワードは設定画面から変更できます。」 | False |
| N1 | 返品 送料 | 资料没有送料承担方，expected_evidence=None | None |
| N2 | 駐車場 | 资料没有停车场信息，expected_evidence=None | None |

R4是有答案但关键词算法漏检的固定案例。现有`retrieve_chunks()`按空白分词，再检查整个词项是否为片段的子串；R4没有空格，整句不在原文中，所以没命中。今天记录这个失败，不改检索器，不把预期改成None以提高分数。

N1会命中包含「返品」的片段，N2没有命中。**expected_evidence=None表示人工确认这份固定资料没有答案，不表示应该返回零片段。** 今天没有生成回答，不能自动给N1/N2填correct_refusal；它们不纳入有答案问题的证据命中比例。

没有新库；只复用dataclass、for、if、字符串`in`、计数和None。字段名的含义：

- `EvalCase`：固定问题与预期；`ExpectedEvidence`：来源名和原句。
- `EvidenceCheck`：同一个case、同一个context和evidence_found。
- `evidence_found=True`：这处预期在发送片段中找到；`False`：有预期却没找到；`None`：没有期望证据，不评分。
- `EvidenceSummary`：总数total、参与比例的evaluated、hits、misses、unscored、hit_rate。

判断None请使用`is None`；区分True/False可以用`is True`/`is False`。不要用一个`if not value`把False和None合在一起。

与作业无关的最小例子：

```python
# 字符串in检查连续文字，不会理解日文同义表达。
print("3日" in "配送には3日かかります。")  # True
print("三日" in "配送には3日かかります。")  # False

# 数据快照与原对象身份是两种检查；这是可单独运行的小例子。
from dataclasses import dataclass, asdict

@dataclass
class Item:
    name: str

records = [Item("apple")]
original = records[0]
before = [asdict(record) for record in records]
# 这里只观察两种比较，未调用今天的TODO。
assert [asdict(record) for record in records] == before
assert records[0] is original
```

Java类比：`source_name == ...`类似字符串`.equals()`；Python的`is`类似Java引用身份比较，不能用`is`比较字符串内容。dataclass注解不会自动检查全部数据；本日输入由已提供代码保证合法，不增加校验练习。

Chrome已核对[Python3.11官方列表copy说明](https://docs.python.org/3.11/tutorial/datastructures.html#more-on-lists)及同页[比较条件](https://docs.python.org/3.11/tutorial/datastructures.html#more-on-conditions)，只需本节用到的浅拷贝、in、is。腾讯课程只对应路线4.1评测基础的固定样例与预期，必要概念已在本节解释，不增加整页阅读或读书报告。

普通调用链：

```text
run_eval_demo.main()
  → evaluation_chunks()：三份自制资料各一块
  → evaluation_cases()：六个事先写好的问题及预期
  → 每个case：
      retrieve_chunks(chunks, case.question, 2)
      → build_context(hits, 500)
      → check_evidence(case, context)
  → summarize_evidence(checks)
  → asdict / json.dumps：一次打印完整报告
```

expected_evidence仅交给检查函数；检索器不接收预期答案。今天不学Embedding、向量库、自动事实评分、LLM-as-judge、Prompt改善、UI、数据库、并发或Docker；不新增真实调用。Docker旧闸门仍未验证，不作为今天追加作业。

## 4. TODO 1：检查发送片段中的期望证据

文件：`code/retrieval_eval.py`，函数`check_evidence(case, context)`。

- 目的：把固定预期与实际准备发送的资料逐例对比。
- 输入：合法EvalCase与ContextBundle，后者来自build_context，text与chunks一致。合法预期的source_name/quote为非空字符串；无需额外处理其他错误类型或不一致的bundle。
- 输出：新的EvidenceCheck；`check.case is case`和`check.context is context`均成立。
- 新增异常：无。删除NotImplementedError占位。
- 处理顺序：先分清有没有期望证据 → 有预期时逐个检查发送片段 → 确定True/False/None → 返回记录。
- 无预期返回None；有预期但空context返回False；同一个片段同时满足完整来源名与完整quote子串才返回True，否则False。不能检查第一块不匹配就提前漏掉后面的匹配块。
- 不修改任何输入值、片段顺序或对象，不重建case/context，不重新检索、不调用模型、不读写文件。
- 验证标准：第2节匹配规则、三态结果、原值和身份保留全部符合；提供测试覆盖不同文件同句、同文件错句、缺标点、跨片段凑条件与第二块才匹配。

只完成TODO1后，全日目标138 passed / 8 failed；剩余为汇总、演示依赖汇总和独立测试。该阶段数量已由助手临时参考核对，不代表你已执行。

```text
.\.venv\Scripts\python.exe -m pytest Week6/day37/tests/test_retrieval_eval.py -k "not summary and not demo" -q
```

## 5. TODO 2：汇总证据检查结果

文件同上，函数`summarize_evidence(checks)`。

- 目的：报告有答案的问题中，有多少期望证据实际进入发送资料。
- 输入：合法EvidenceCheck列表，evidence_found只为True、False、None；每项独立计数，case_id重复也计数，本日不做去重。
- 输出：新的EvidenceSummary；新增异常：无。

| 字段 | 完整要求 |
|---|---|
| total | 输入记录条数 |
| hits | evidence_found为True的条数 |
| misses | evidence_found为False的条数 |
| unscored | evidence_found为None的条数 |
| evaluated | hits + misses（不是total） |
| hit_rate | evaluated > 0时hits / evaluated；否则None，不乘100、不四舍五入 |

处理步骤：建立本次计数 → 逐条区分三态并计数 → 算evaluated和比例 → 返回完整汇总。每次调用独立，不使用累计状态，不修改或排序输入。边界由你实现：空输入、全部None都不做除法；有参与评分样例但全miss才是0.0。

固定六题的完整结果应为`total=6, evaluated=4, hits=3, misses=1, unscored=2, hit_rate=0.75`。比例只说明这四个有答案问题的期望证据覆盖情况，不是模型回答准确率，也不是所有RAG任务的通用Recall指标。

两个函数完成后，全日目标145 passed / 1 failed，仅剩独立测试；全部完成目标146 passed。

```text
.\.venv\Scripts\python.exe -m pytest Week6/day37/tests/test_retrieval_eval.py -q
```

## 6. TODO 3：独立验证“命中却没发送”

文件：`tests/test_day37_extra.py`，完成已命名测试并删除pytest.fail。具体子模块导入：

```python
from dataclasses import asdict
from Week6.day37.code.context import build_context
from Week6.day37.code.eval_cases import evaluation_cases, evaluation_chunks
from Week6.day37.code.retrieval import retrieve_chunks
from Week6.day37.code.retrieval_eval import check_evidence
```

不需要配置`__init__.py`。这是无网络的普通函数测试，不需要monkeypatch。

输入和操作顺序：

1. `cases = evaluation_cases()`，取`case = cases[0]`（R1）；`chunks = evaluation_chunks()`，三块顺序与资料列表相同。
2. **调用检索前**保存case完整asdict快照、chunks各项asdict快照，以及原片段引用（例如`original_chunks = chunks.copy()`）。
3. `hits = retrieve_chunks(chunks, case.question, 2)`；应恰好一条命中，为returns_faq.txt原片段。
4. 对同一份hits，依次建立`full = build_context(hits, 500)`、`tiny = build_context(hits, 1)`，各调用一次check_evidence。1字符放不下任何完整资料块。
5. 所有调用结束后进行断言。

必须验证：

- hits长度为1，`hits[0].chunk is original_chunks[0]`；两次检查后hits仍是这条命中，不能靠清空hits伪造预算结果。
- full.chunks完整列表等于`[original_chunks[0]]`，且其中对象`is original_chunks[0]`；tiny的完整asdict等于`{"text": "", "chunks": []}`。
- 两份EvidenceCheck的**完整asdict**分别等于`{"case": asdict(case), "context": asdict(full), "evidence_found": True}`及tiny/False对应字典；不是只看布尔值。
- 两份check.case分别`is case`，两份check.context分别`is full`、`is tiny`。
- 最后case完整值、chunks完整值与顺序均和调用前快照一致；三个位置仍分别`is original_chunks[0/1/2]`。

本题额外验证已给定的预算边界，不需要改算法或编造生成回答。输入快照检查值，is检查原对象；不要把asdict字典列表与Chunk对象列表直接比较。

## 7. 最后验收与复盘

```text
.\.venv\Scripts\python.exe -m pytest Week6/day37/tests -q
.\.venv\Scripts\python.exe -m Week6.day37.code.run_eval_demo --help
.\.venv\Scripts\python.exe -m Week6.day37.code.run_eval_demo
```

- 当前日全部测试通过；help退出0。正常演示退出0，输出一行完整UTF-8 JSON，顺序R1/R2/R3/R4/N1/N2；evidence_found为true/true/true/false/null/null。
- retrieved_count依次为1/1/1/0/1/0；summary见TODO2；gateway_calls=0，dataset_origin为provided_synthetic_faq_v1。不生成文件、不需要密钥。
- R4的miss是成功执行得到的基线结果，正常退出0，不为达到1.0去改样例、问题或旧检索器。
- 两个TODO未实现时入口提示并退出1、无traceback；非法参数由argparse退出2。

在笔记中填写三题复盘、自报实际用时、难度与仍需讲解位置，再请助手验收本日。测试通过只证明这些工程行为。以上为建立时的学习顺序；本日当前验收结论见第9节。

## 8. 助手建立验证（不是学习者必做历史回归）

以下为2026-10-15建立材料时的历史状态，当前完成结论见第9节。

- Python3.11.15、pip check通过；复制后新增练习前128 passed。
- 初始129 passed / 17项预期TODO失败，无警告。临时参考仅TODO1时138 passed / 8 failed；两个函数时145 passed / 1 failed；连同独立测试的临时参考146 passed，无警告。参考代码只在临时进程内，未写入练习，不是学习者完成证据。
- 实际子进程help/未实现/非法参数退出0/1/2，无traceback；临时参考正常入口退出0，一行完整UTF-8 JSON、六题顺序、各项结果与0.75汇总、零调用正确。所有入口在临时工作目录运行，没有生成输出文件。
- 本日没有历史目录迁移、共享代码修改或跨日导入，无需全仓重跑。UTF-8、文档链接、当天导入、差异空白和敏感模式检查在交付前核对。
- 建立时两个核心TODO与独立测试占位保留，未完成学习、未提交推送；当时开始时间、实际用时和复盘等待学习者填写。

## 9. 最终验收（2026-10-16）

- 学习者完成两个核心函数和独立预算测试，146 passed、无警告，pip check通过；同来源完整原句匹配、True/False/None、空输入与全不评分分母、连续调用、完整值快照和原对象保留均符合原要求。无需修改核心算法或补独立断言。
- 实际子进程help/正常/非法参数退出0/0/2；一行完整UTF-8 JSON、资料来源与六题顺序、命中数1/1/1/0/1/0、结果True/True/True/False/None/None、total=6/evaluated=4/hits=3/misses=1/unscored=2/hit_rate=0.75、零调用均通过，无traceback或输出文件。R4是固定基线漏检，正常执行仍退出0。
- 复盘第1题和第2题数值正确；第2题关于拒答的措辞已改清楚，学习者已正确指出今天未调用LLM且没有实际回答，不把题目歧义算作学习者错误。第3题的检索限制与不能篡改预期判断正确；最后一答将评测对象说成LLM回答，由助手补准为人工期望原句与发送资料的比较，不作为已独立巩固的证据，不要求重抄。
- 自报实际用时“1h-”、简单、仍需讲解无；开始0504保留，结束时间见笔记最后一行，不根据起止差值推算。助手仅补中文块注释、清理未使用pytest导入、修订题目与整理记录，没有代写核心函数或独立断言，没有读取Cmder日志。
- 下次Day38先用R1短复习“expected_evidence.quote→context.chunks中的同来源原片段”，再沿固定评测集与可验证改善的主线安排适量同主题实践；不补交旧题。历史副本除本日日名/导入替换外保持一致，无共享逻辑或目录迁移，不要求重跑全仓。按项目默认规则提交推送，上传以实际远端核对为准。
