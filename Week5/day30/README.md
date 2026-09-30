# Day30 — 按问题检索已切好的片段

状态：2026-09-30 已完成并验收。本日只做本地关键词检索与排序，不调用模型或网络。以下 TODO 与初始失败保留为历史练习说明。

## 0. 按顺序开始

1. 在 [学习记录](./day30_notes.md) 填开始时间。以下命令在**仓库根目录**执行，PowerShell 或 CMD/Cmder 均可，使用根目录 Python 3.11 `.venv`。
2. 先运行初始脚手架检查：

   ```text
   .\.venv\Scripts\python.exe -m pytest Week5/day30/tests -q --tb=no
   ```

   预期 **12 passed、10 failed，退出码 1**。12 项是 Day29 切块代码复制到 Day30 后的旧行为；9 项因 `retrieve_chunks()` 尚未实现，1 项是你要写的独立测试占位。这些失败是预期练习状态，实现后不用回退重现。
3. 先读第 1～2 节和非测试代码 `code/chunking.py`、`code/retrieval.py`，再读 `tests/`。特别看清：`chunk_documents()` 产生 `Chunk`；`retrieve_chunks()` **接收已有 Chunk**，不重新切文档。
4. 完成第 3 节两个 TODO，期间运行当天测试；最后按第 4 节验收、填写复盘及自报用时，再交助手检查。

## 1. 用 Day29 一个例子分清两个调用（5 分钟）

`chunk_document(Document("faq.txt", "退货期限为30天。"), 20, 0)` 返回带出处的 `Chunk`。这一步没有接收客户问题。今天才把这些 `Chunk` 和问题字符串一起交给 `retrieve_chunks()`，选出文字匹配的片段。检索命中只说明规则选中了片段，还没有生成回答，也没有证明回答正确。本日无需补交 Day29 复盘。

## 2. 最小知识与调用链（15～20 分钟）

```text
Document → chunk_documents() → list[Chunk]
                                ↓
                    retrieve_chunks(chunks, query, top_k)
                                ↓
                  list[RetrievalHit(chunk, score)]
```

`query` 是问题文字，`top_k` 是最多返回几块。今天的简易规则把问题按空白拆成词项；日文无空格短语（如 `返品期限`）是一个词项，不做日文分词。每个不同词项在片段文字中出现，就加 1 分；同一词项重复出现或问题中重复写，不重复加分。例如问题 `返品 30日`，片段 `返品は30日以内` 得 2 分，`返品の案内` 得 1 分。0 分片段不返回；同分保持输入顺序，最后取前 `top_k` 个。

你只需用到 `str.split()`、`str.casefold()`、子串成员判断、`set` 或等效去重，以及 `sorted(..., key=...)`。例如 `"  Refund  policy ".split()` 得 `['Refund', 'policy']`；`"REFUND".casefold()` 与 `"refund"` 相同。Python 的稳定排序会保留相同排序键的原有次序，类似 Java 的稳定排序；这里仅依赖这个排序性质，不把 Python 字符串的子串匹配等同于语义理解。参考 [Python 3.11 字符串方法](https://docs.python.org/3.11/library/stdtypes.html#str.split) 与 [排序稳定性](https://docs.python.org/3.11/howto/sorting.html#sort-stability-and-complex-sorts)，只需看上述行为。

局限：空白拆词不能理解同义词、日文词边界或问题语义；重叠切块可能让相同内容多次命中。今天不学 embedding、向量库、模型生成、引用展示、语义评测或 Docker；Week4 的 Docker 实跑要求仍待环境可用时验证。

## 3. 两个 TODO（约 55～70 分钟）

### TODO 1：实现 `code/retrieval.py` 的 `retrieve_chunks()`

目的：从已切好的片段中选出与问题文字匹配的片段。只改该函数。输入：`list[Chunk]`、`query: str`、`top_k: int`；输出：`list[RetrievalHit]`，每项保留原 `Chunk` 及整数 `score`。不读写文件、无 CLI/退出码、无网络。

处理顺序：

1. 即使 `chunks` 为空，也先验证参数：`query.split()` 没有词项时抛 `ValueError("invalid_query")`；否则若 `top_k <= 0`，抛 `ValueError("invalid_top_k")`。错误消息必须精确一致。
2. 对 `query.split()` 的词项做 `casefold()` 并去重。用 `chunk.text.casefold()` 判断每个不同词项是否是子串。只检查 `text`，文件名和块编号不参与评分。得分是匹配的**不同词项数**，不是出现次数。
3. 得分 0 的片段丢弃；得分大于 0 的构成 `RetrievalHit(chunk, score)`。按分数从高到低排；同分按传入 `chunks` 的顺序。排序后最多返回 `top_k` 项。不要修改传入列表或 `Chunk`，也不要丢失来源文件名、字符范围与块编号。

完成标准：日文短语、英语大小写、重复词项、无命中、空片段列表、非法参数、排序和 `top_k` 均符合契约；Day29 复制来的切块测试仍通过。

### TODO 2：写 `tests/test_day30_extra.py` 的并列边界测试

目的：自己验证同分时按**传入顺序**截取，而不是按文件名、块编号排序。只替换占位测试。构造三个 `Chunk`，按 `z.txt`、`a.txt`、`m.txt` 的顺序传入；三个 `text` 分别为 `"返品案内"`、`"返品期限"`、`"返品受付"`，`chunk_index` 可都为 0，`start=0`，`end=len(text)`。以 `query="返品"`、`top_k=2` 调用后，断言返回的文件名顺序为 `["z.txt", "a.txt"]`、分数为 `[1, 1]`，且结果里的 `chunk` 就是前两个传入对象。此测试无业务返回值；断言通过时 pytest 退出 0，失败时退出 1。

## 4. 实现后验收与复盘（15～20 分钟）

在仓库根目录运行：

```text
.\.venv\Scripts\python.exe -m pytest Week5/day30/tests -q
```

目标 **22 passed**。助手检查当天文件与差异后复测，并核查排序、来源保留和无命中行为；这次不要求学习者重跑所有旧天测试。`[]` 的含义只是按本日关键词规则没有命中，不能直接等同于“文档里没有答案”。实现和复盘均验收后才标记 Day30 已完成。

## 5. 助手建立记录（非学习者必做）

- Day29 所需代码和测试已复制到 Day30，导入路径改为 `Week5.day30`；Day29 历史文件未修改。
- 初始当天实测 12 passed / 10 项预期 TODO 失败；排除 Day30 的全仓历史测试为 1004 passed。`git diff --check` 通过；Day30 文件的敏感模式扫描未发现匹配。此记录只说明脚手架建立，不代表 TODO 已实现。
- 2026-09-30 最终验收：学习者完成检索函数和同分边界测试，补齐返回原对象的两项 `is` 断言；本日 22 passed。手动核查输入不变、原对象保留、文件名不参与评分通过。复盘原答保留，第 2 题的错误排序结果已追加澄清；自报用时 1.5h、难度简单。本日证据仅限关键词检索，不证明语义检索或回答质量。
