# Day29 — 给文档切块并保留出处

状态：2026-09-29 已完成并验收。本日唯一主题是把本地文档文本分成可追溯的片段；不调用模型或网络。以下 TODO 与初始失败保留为历史练习说明。

## 0. 按顺序开始

1. 在 [学习记录](./day29_notes.md) 填开始时间。以下命令从**仓库根目录**运行，适用于 PowerShell 和 CMD/Cmder，使用根目录 Python 3.11 `.venv`。
2. **先运行初始脚手架检查**：

   ```text
   .\.venv\Scripts\python.exe -m pytest Week5/day29/tests -q --tb=no
   ```

   预期 **12 failed，退出码 1**：11 项针对尚未实现的 `chunk_document()`，1 项是留给你写的独立边界测试。它们是预期 TODO 失败，不是已完成代码的故障。实现后无需回退代码重现。
3. 读第 1～2 节，再看非测试代码 `code/chunking.py` 的 `Document`、`Chunk`、`chunk_document()`、`chunk_documents()` 调用关系，最后看 `tests/`。开始 TODO 前，确认 `chunk_documents()` 只是按输入顺序调用单文档函数并合并结果。
4. 实现时重跑当天测试；按第 4 节验收，填写学习后复盘、实际用时和难度，再交助手检查。

## 1. Day28 只复习一个例子（5 分钟）

报告顺序为 A、B；A 的合法原文含 `CSV`，给 A 写了“必须含 `PDF`”的预期；B 调用成功，但没有写预期。`audit_batch()` 应返回 A 的 `content_failed / ["missing:functions:PDF"]`，随后 B 的 `not_checked / []`。**预期决定检查条件，报告决定结果顺序。**这两个状态不能因为原文存在就都算通过。Day28 已结束，这里无需补交旧复盘。

## 2. 最小知识与调用链（15～20 分钟）

RAG 的长链路是“导入 → 切块 → 索引 → 检索 → 生成 → 引用”。今天只做第二步，并为未来引用留下出处：

```text
Document(source_name, text)
  → chunk_documents() 按文档顺序调用 chunk_document()
  → Chunk(source_name, chunk_index, start, end, text)
  → 将来可用 source_name + [start:end] 找回原文
```

`Document` 类似 Java/Kotlin 的小型只读数据对象；`Chunk` 的 `start` 包含该位置，`end` 不包含该位置。例如 `"ABCDE"[1:4]` 得到 `"BCD"`。切块不改变原文，不 `strip()`，因此日文、空格、换行都留在原文位置。`len()` 和切片按 Python 字符串索引计数，本题不使用 UTF-8 字节位置。`frozen=True` 限制字段重新赋值，但不等于所有嵌套对象都深度不可变。本日只需这些语法。

示意：原文 `ABCDEFGHIJK`、每块最多 5 个字符、相邻块重叠 2 个字符时，三个范围是 `[0:5]`、`[3:8]`、`[6:11]`。末块到达原文结尾就停止，即使重叠仍可再切出较短尾巴，也不要生成重复尾块。这里的重叠用于减少边界处上下文断裂，但固定字符窗口可能切断句子；这是本日策略的已知局限，不代表检索或回答已经正确。

可按需查 [Python 3.11 字符串切片](https://docs.python.org/3.11/tutorial/introduction.html#strings) 和 [Python 3.11 dataclass](https://docs.python.org/3.11/library/dataclasses.html)，上面的例子已包含本日需要的部分。今天暂不学分词器、embedding、向量库、检索排序、生成、引用格式或 Docker。Week4 的 Docker 可运行要求仍待有环境时实际验证，不用本日离线测试替代。

## 3. 两个 TODO（约 50～65 分钟）

### TODO 1：实现 `code/chunking.py` 的 `chunk_document()`

目的：把**一份**本地文档按字符窗口切块，并给每块可回查的出处。只改这个函数。输入：`Document(source_name: str, text: str)`、整数 `max_chars`、整数 `overlap_chars`。输出：`list[Chunk]`；没有 CLI 或退出码，不读写文件，不调用网络。

处理顺序和契约：

1. 先检查参数：`max_chars > 0`，且 `0 <= overlap_chars < max_chars`；否则抛 `ValueError("invalid_chunk_size")`。即使原文为空也先检查参数。
2. 有效参数下，空原文返回 `[]`。非空原文从 `start=0` 开始，每块 `end=min(start + max_chars, len(text))`，`text` 必须**精确等于** `document.text[start:end]`，不得去空格或改行尾。
3. 每块的 `source_name` 取自输入文档；`chunk_index` 从 0 连续递增。追加本块后，若 `end == len(text)`，立即停止；否则下一块 `start=end-overlap_chars`。因为重叠小于块长，起点会前进。
4. 不修改输入。`chunk_documents()` 已提供，会依输入文档顺序调用你的函数；每份文档的编号重新从 0 开始，不要把多份文档当作一份文本拼起来。

完成标准：普通、日文、空文本、刚好一块、重叠、非法参数、多文档顺序均符合上面的范围和字段；当天测试通过。

### TODO 2：写 `tests/test_day29_extra.py` 的边界测试

目的：独立证明重叠几乎占满窗口时，起点仍前进且最后停止。只替换占位测试，不改已提供测试。输入 `Document("edge.txt", "ABCDE")`、`max_chars=3`、`overlap_chars=2`。调用 `chunk_document()` 后，断言准确的 `(start, end, text)` 三元组列表为 `(0,3,"ABC")`、`(1,4,"BCD")`、`(2,5,"CDE")`；编号为 `[0,1,2]`，并对每块断言 `chunk.text == document.text[chunk.start:chunk.end]`。测试函数没有业务返回值；断言成功时 pytest 退出 0，失败时退出 1。这项额外边界与主主题相同，不增加新库。

## 4. 实现后验收与复盘（15～20 分钟）

从仓库根目录运行：

```text
.\.venv\Scripts\python.exe -m pytest Week5/day29/tests -q
```

目标 **12 passed**。助手会先看你当天文件和差异，再运行测试，并检查相邻切片没有漏字、最后一块可回查原文、多文档出处不混淆。学习者无需重跑已完成日的全部测试。离线测试只证明切块契约，不证明 RAG 检索、引用或模型回答质量。完成后在笔记中回答下方复盘题，自报实际用时和难度。只有实现、测试和复盘验收完成后，才将 Day29 标为“已完成”。

## 5. 助手建立记录

- Week4 已按 Day22～28 归档，原文件和导入路径保持不变；Day29 是新 RAG 组件，没有调用 Day28 业务代码，因此不复制旧代码。
- 新增纯标准库脚手架、11 项函数契约检查与 1 项独立边界测试占位。助手初始实测为本日 **12 项预期 TODO 失败**，全仓 **992 passed / 同 12 项失败**；Day28 单独复测 **134 passed**。旧学习日测试保持通过。初始失败不代表学习者已完成。
- 2026-09-29 完成验收：学习者实现固定字符切块和高重叠边界测试；本日 **12 passed**，助手全仓回归 **1004 passed**、`pip check` 通过。复盘中的超前问题已订正为当前代码范围，原答保留；代码通过不代表已具备检索或模型回答能力。
