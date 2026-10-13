# Day35 — 把回答里的编号对应到原资料

状态：已完成（2026-10-14 验收）。唯一主题是**根据回答写出的编号，找到本次发送的原资料片段**，让人能并排查看回答和原文。参考 90～120 分钟，优先把一个例子讲清，不机械凑时长。下方 TODO 与初始失败描述保留为作业契约和历史起点，最终结论见第 8 节。

Day34 已完成，自报 2h+、难度难、编号仍抽象。今天先用其真实 A/B 记录复习，不补交旧题、不重复模型请求。代码和 93 项既有测试复制自 Day34，导入与 monkeypatch 路径均改为 `Week5.day35`；历史目录不修改。新实现只需一个小函数和一个独立边界测试，无新依赖。

## 1. 按这个顺序开始

工作目录：仓库根目录。以下单行命令适用于 **PowerShell 与 CMD/Cmder**，均使用根 `.venv` 的 Python 3.11。

1. 在 [学习记录](./day35_notes.md) 填开始时间，不需要提前回答概念题。
2. 先做一次初始脚手架检查，再读第 2～3 节的具体例子。

```text
.\.venv\Scripts\python.exe -m pytest Week5/day35/tests -q
```

初始预期 **93 passed / 12 failed**，退出 1。新函数与独立测试尚未实现，失败来自 TODO 占位，属于作业起点；原有 93 项已通过。实现后不必退回初始状态。

3. 只改第 4～5 节指定的两个文件，运行测试。
4. 完成后运行离线对照演示，核对原文并填写两题复盘、自报实际用时。

## 2. 先把实际的 [1] 看清楚

Day34 真实调用记录中的资料如下（本日只离线回看）：

```text
[1] returns_faq.txt (0:28)
返品期限は30日です。
開封済みの商品は返品できません。
```

`build_context()` 在发送资料前加上 `[1]`。这个 `[1]` 表示“**本次发送资料列表中的第一块**”，人和模型可以用它指向这段资料。它不是永久文档 ID，也不是模型调用次数。

| 位置 | 本例的具体值 | 表示什么 |
|---|---|---|
| context.text 中的 `[1]` | 资料头部的文字 | 给这次资料第一块标号 |
| context.chunks[0] | returns_faq.txt 的原 Chunk 对象 | Python 下标 0 是列表第一项 |
| Chunk.chunk_index | 0 | 该片段在原文档内的切块序号；不是回答引用编号 |
| A 回答末尾的 `[1]` | `返品期限は30日です。[1]` | 回答指向这次资料第一块 |

只有一块时容易把几个数字混在一起。先固定看这个对应关系：

```text
回答文字中的 [1]
       ↓ 指向本次发送资料的第一块
context.chunks[0]
       ↓ 读对象的 source_name、start、end、text
returns_faq.txt，0:28，返品期限は30日です。……
       ↓ 人工对照
回答中的 30 日确实在这段原文中
```

Day34 的 B 问“返品 送料”，回答是 `資料からは回答できません。`，没有写 `[数字]`。资料仍然发送了一块，但是**回答没有指向哪块资料**：从回答提取的编号列表为 `[]`，今天取出的引用片段也为 `[]`。原文没写送料由谁承担，因此本次拒答合理。既有 `missing_citation` 只描述缺编号，继续保留，不修改判断规则。

如果把 A 改成示意回答 `返品期限は90日です。[1]`，程序仍能找到同一个原片段；人工会发现它与“30日”冲突。**能找到资料，不等于这段资料支持回答。** 今天不让普通 Python 函数理解日文事实。

## 3. 只需要这些已有知识

今天不引入新库。列表下标从 0 起，负下标会从末尾取值；所以引用 `[0]` 不能当成合法引用去索引列表。这些规则已用 Chrome 核对 [Python 3.11 序列操作](https://docs.python.org/3.11/library/stdtypes.html#common-sequence-operations)，只需关注 `s[i]`、`len(s)`、`in` 和负下标说明，不用通读文档。

与作业不同的最小例子：

```python
names = ["甲", "乙"]
names[0]       # 第一项是“甲”；类似 Java List.get(0)。
names[-1]      # Python 可以取末项；Java List.get(-1) 会出错，类比到这里不同。
seen = []
seen.append(7) # 给当前列表追加一个数字。
7 in seen      # True；可以用数字列表记住已经处理过的编号。
```

`extract_citation_ids(answer)` 已在 `code/citations.py` 实现：`"説明。[2][01][2]"` 得到 `[2, 1, 2]`。`[01]` 与 `[1]` 是同一编号，不要重写正则。返回类型 `list[Chunk]` 表示返回片段对象列表；不是编号列表、文件名列表或 JSON。

先读非测试代码：`code/context.py` 的 `ContextBundle`，再读 `code/citations.py` 的提取函数，最后看今天的 `code/citation_sources.py`。不必重新从 HTTP 入口跟到网关。

今天的普通调用链：

```text
run_source_demo.main()
  → 用已有 build_context() 建立这次资料
  → 将记录中的 answer 和 context 传给 find_cited_chunks()
      → 使用已提供的 extract_citation_ids()
      → 返回回答引用的原 Chunk 对象
  → 将原回答、编号错误、引用原文分别打印
```

测试直接调用 `find_cited_chunks()`，没有外部依赖需要替换。今天不学新 HTTP 结构、异步、回调、模型 SDK、Embedding、向量库、自动事实评分、拒答例外、Web 页面或 Docker；也不新增腾讯课程读书报告。

## 4. TODO 1：取出回答引用的原片段

修改 `code/citation_sources.py` 的 `find_cited_chunks(answer, context)`。

- 目的：为人工核查提供回答实际引用的原文，不自动评价正确性。
- 输入：回答字符串 `answer`，由已有 `build_context()` 建立的合法 `ContextBundle`；只使用这次 `context.chunks`，不使用检索命中列表或其他文件。
- 输出：新的 `list[Chunk]`，元素必须是 `context.chunks` 内的**原对象**，不重新构造 Chunk。
- 按回答中编号首次出现的顺序返回；同一编号只取一次。`[2][1][2]` 对应先第二块、再第一块。
- 有效编号为 `1` 到 `len(context.chunks)`，引用编号减 1 对应 Python 列表下标。越界编号跳过，之后的合法编号仍要处理；不能误用 Python 负下标。`[0]` 始终无效；本次仅有两块时 `[99]` 无效，本次有至少 99 块时 `[99]` 有效，不是固定禁用编号。
- 无编号、空回答、只有未知编号或 context 没有片段时返回 `[]`，不抛编号越界异常。`[01]` 由现有提取函数按 1 处理。
- 处理步骤：提取编号；按出现顺序逐个处理；检查是否有效、是否处理过；取原片段放入新的结果列表；所有编号处理完后返回。
- 不修改 answer、context.text、context.chunks 的内容或顺序；不改 `check_citations()`，不调用模型、不读取文件、不写文件。合法输入不新增异常或错误消息契约。

完成标准：提供的 **11 项**资料定位测试全部通过；此时全日 **104 passed / 1 failed**，剩余为独立测试占位。

```text
.\.venv\Scripts\python.exe -m pytest Week5/day35/tests/test_citation_sources.py -q
```

## 5. TODO 2：独立验证引用编号不是原文块序号

修改 `tests/test_day35_extra.py`，实现已命名的测试。目的：在两个数字刻意不一致时，证明程序按**本次发送位置**找资料。

输入由你在测试内创建：

```text
first  = Chunk("a.txt", 7, 0, 2, "返品")
second = Chunk("b.txt", 3, 0, 2, "送料")
hits   = [RetrievalHit(first, 1), RetrievalHit(second, 1)]
context = build_context(hits, 500)
answer = "送料の説明。[2][2][99][0]"
```

这里的“对应模块”指类或函数所在的具体 `.py` 文件，不是直接从 `code` 包导入。请在测试文件顶部使用：

```python
from Week5.day35.code.chunking import Chunk                 # chunking.py 中的原文片段类。
from Week5.day35.code.retrieval import RetrievalHit         # retrieval.py 中的检索命中类。
from Week5.day35.code.context import build_context          # context.py 中的资料整理函数。
from Week5.day35.code.citation_sources import find_cited_chunks  # 今天要验证的定位函数。
```

`code/__init__.py` 保持为空即可，无需配置或添加导出。`from Week5.day35.code import Chunk` 会从包本身查找 Chunk；当前包没有导出这个类，所以不能这样写。以上写法直接定位具体模块里的名字，与 Java 按类所在包导入有相似之处，但 Python 的模块还可以导入普通函数，并不完全等同于 Java。

这四个导入都来自本日副本，不导入历史日代码。测试没有网关或联网操作。

执行前保存 `context.text` 和 `context.chunks.copy()`，然后调用一次 `find_cited_chunks(answer, context)`。

必须断言：完整结果恰好为 `[second]`，结果第一项 `is second`；context.text 未变，context.chunks 完整值与顺序未变，两项仍分别 `is first`、`is second`。这些断言分别验证不多取、原对象保留、输入保留。有效输入应正常返回，不预期异常。

如果错误实现把 `[2]` 当成 `chunk_index == 2`，本例两个对象的 chunk_index 为 7 和 3，它会取不到 second，完整结果断言会失败。失败能发现行为不符，不能仅靠断言自动诊断所有错误的根因。

完成标准：独立测试通过，全日目标 **105 passed，无警告**。

## 6. 运行演示并做一次人工对照

```text
.\.venv\Scripts\python.exe -m pytest Week5/day35/tests -q
.\.venv\Scripts\python.exe -m Week5.day35.code.run_source_demo --help
.\.venv\Scripts\python.exe -m Week5.day35.code.run_source_demo
```

实现完成后：测试退出 0；help 退出 0；演示退出 0，输出三行 UTF-8 JSON，不生成文件、不需要密钥。新函数未实现时，演示只打印 TODO 提示并退出 1；非法命令参数由 argparse 退出 2。

| case | 原回答来源 | cited_chunks | citation_errors | 人工对照目标 |
|---|---|---|---|---|
| A | Day34 已记录真实回答 | 一块 returns_faq.txt | `[]` | 原文的 30 日支持回答 |
| B | Day34 已记录真实拒答 | `[]`，context 仍有一块 | `["missing_citation"]` | 原文没有送料承担方，拒答合理 |
| wrong_90 | 本日示意反例 | 与 A 相同的一块 | `[]` | 原文写 30 日，回答 90 日与其冲突 |

三行的 `gateway_calls` 均为 0，表示**本日演示**没有调用模型；不改写 Day34 A/B 当时各调用一次的历史事实。`answer_origin` 区分记录与反例，定位后的片段保留来源、原文位置与文本。原回答不自动改写。

今日完成须包含：105 项测试、上述演示核对、学习后两题复盘和自报用时。不以编号检查通过当成事实正确，不要求重复真实调用或重跑全部历史日。学习者实现与记录验收后，按项目规则提交推送；当前材料建立不算完成。

## 7. 助手建立验证（非学习者必做）

- 复制当天代码和测试后、新增 TODO 前 93 passed；根 Python 3.11.15，pip check 通过。
- 新增练习后初始 93 passed / 12 项预期 TODO 失败；核心实现与独立测试留给学习者。
- 当前无需目录迁移或共享逻辑修改，不要求全仓回归；临时参考验证和入口检查见学习记录，不当成学习者完成证据。

## 8. 最终验收（2026-10-14）

- 学习者完成核心函数与独立测试，105 passed，无警告，pip check 通过。首次引用顺序、set 只记录已处理编号、有效上限包含最后一块、未知编号过滤、原对象及输入保留均符合契约；额外人工验证本次有100块时99与100可引用，0与101跳过。
- 实际离线模块的 help、正常演示、非法参数分别退出0、0、2；三行 UTF-8 JSON 的来源、位置0:28、原答案、资料与引用片段列表、错误列表和零调用符合任务单，无 traceback、无输出文件。A 的30日有据；B 的资料未写送料，拒答合理；90日示意回答引用存在但与原文冲突。未重复真实模型调用。
- 复盘原答保留，第2题结论与支持句正确；第1题的对象选择和无效0判断正确，完整列表格式及“按本次发送顺序，独立于原文chunk_index”的理由由助手补准，详见学习记录，不冒充独立复盘证据。实际用时自报1h、难度中，无仍需讲解的位置。
- 助手只补中文块注释、整理空白并更新文档状态，核心算法和独立断言由学习者完成。下一日进入Week6 / Day36，先用今天两个chunk_index不同的对象短复习，再沿问答依据核查主线确定同主题适量练习，不补交旧题；Week4 Docker 闸门仍未验证。
