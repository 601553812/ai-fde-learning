# Day33 — 检查回答中的引用编号

状态：已完成（2026-10-11 验收通过）。唯一主题：核对回答里的资料编号是否存在于**本次实际发送的上下文**。参考 90～120 分钟，根据理解情况调整，不凑时长。Day32 自报 2H、难度难，因此今天只新增一个核心函数和一个独立测试；不补交昨天复盘。完全离线、无新依赖，不要求密钥。下方 TODO、初始失败和“待填写”描述是原作业与建立过程，当前结果见末尾验收记录。

## 0. 按顺序开始

1. 在 [学习记录](./day33_notes.md) 填开始时间；先不用回答复盘题。
2. 在**仓库根目录**运行下面单行命令，PowerShell、CMD/Cmder 均可，使用根 Python 3.11 `.venv`：

   ```text
   .\.venv\Scripts\python.exe -m pytest Week5/day33/tests -q --tb=no
   ```

   初始预期 **56 passed / 13 failed，退出码 1**。52 项来自 Day32，另 4 项验证已提供的提取函数和无资料跳过检查；12 项因核心函数尚未实现失败，1 项是独立测试占位。这是练习初始状态，不是项目故障；完成后不用回退。
3. 阅读下面第 1～3 节，然后按顺序看非测试代码：`qa_service.py` → `citations.py` → `run_citation_demo.py`。切块、检索、预算和请求构造仅按需回查，不从头学一次。
4. 完成第 4 节核心函数，运行对应测试；再做第 5 节独立测试，运行当天测试与演示，最后填写笔记。已有函数、辅助函数、包装函数和演示无需重写。

## 1. 先用昨天一个例子衔接（约 5 分钟）

只有 `faq.txt` 的 `返品期限は30日` 时，昨天整理后实际发送：

```text
[1] faq.txt (0:8)
返品期限は30日
```

- 若预算只有 1 字符，整块放不下：`status="no_context"`，固定提示 `資料からは回答できません。`，网关调用为 0。
- 若预算 100，网关固定返回 `返品期限は90日です。[99]`：昨天仍返回 `status="generated"` 和原文字，调用为 1。`generated` 仅说明返回了文字。

今天在第二种路径返回后增加编号检查：这次只有资料 `[1]`，因此 `[99]` 是未知引用。即使把 `[99]` 改成 `[1]`，仍不能证明“90日”来自原文。先分清这两个检查范围，不要求重答昨天的问题。

## 2. 从普通函数调用看今天的变化（约 10～15 分钟）

```text
answer_question(...)              ← Day32 已完成的当天副本
  → 检索 → 整理资料
  → 无资料：固定提示，零网关调用
  → 有资料：构造请求，调用网关一次，返回 QAResult
                       ↓
review_qa_result(result)           ← 已提供，只决定是否检查
  → no_context：返回 []，跳过检查
  → generated：check_citations(result.answer, result.context)
                         ↓
                    list[str] 引用错误
```

`result.answer` 是返回文字；`result.context.chunks` 是本次真正发送的原片段列表。若其中有两块，对应的合法编号就是 1、2；**不是**原输入列表长度、检索命中数、`chunk_index` 或文件名里的数字。资料整理已经保证纳入后的编号连续。

`review_qa_result()` 是普通函数，它直接调用你要实现的 `check_citations()`。没有框架自动帮你调用，也没有再次调用模型。返回的错误列表与原 `QAResult` 分开保存，不改写原答案和 `generated` 状态。你不需要实现新的数据类。

返回类型 `list[str]` 可类比 Java 的 `List<String>`；只是 Python 类型标注不会像 Java 编译器一样自动限制所有运行时值。这里每个字符串表示一条具体检查结果：`[]` 没有编号错误，非空列表需要核查。

## 3. 今天需要的最小知识（约 10 分钟）

### 已提供：提取编号

`extract_citation_ids(answer)` 接收字符串，返回整数列表，保留出现顺序和重复：

```python
from Week5.day33.code.citations import extract_citation_ids

assert extract_citation_ids("説明。[2][01][2]") == [2, 1, 2]
assert extract_citation_ids("引用なし") == []
```

本日只识别半角方括号中的 ASCII 数字：`[0]`、`[1]`、`[10]`；`[01]` 转成整数 1。`[abc]`、`[１]`、`[-1]`、`[1,2]` 不匹配。规则是简单文字扫描，不是完整 Markdown 解析；代码块或普通文字中出现匹配格式也会被提取。

内部使用 `re.findall()` 找到数字字符串，再调用 `int()` 转换。你只需要理解输入输出，不需要掌握正则写法。可选回查 [Python 3.11 re.findall](https://docs.python.org/3.11/library/re.html#re.findall)，不用通读。

### 沿用：列表长度、成员判断与追加

下面只示范普通列表操作，不是 TODO 的完整实现：

```python
names = ["faq.txt", "guide.txt"]
assert len(names) == 2          # 列表有两项，不是两份文字的总字符数。
seen = [7]
assert 7 in seen               # 类似 Java List.contains(7)。
assert 8 not in seen
seen.append(8)                 # 类似 Java List.add(8)，改变这个列表。
assert seen == [7, 8]
```

`[]` 在条件判断中为假；`in` 判断值是否出现，不能判断对象是否为同一个实例。这些用法见 [Python 3.11 序列操作](https://docs.python.org/3.11/library/stdtypes.html#common-sequence-operations)，只回查 `len`、`in`、列表 `append`。

今天不学：正则表达式全套语法、Markdown 解析、embedding、向量库、真实 Gemini 适配、重试、FastAPI、自动语义评测、提示注入防御。没有新增腾讯课程阅读报告。真实问答后续再接入；当前替身不推理，不把离线通过记成模型效果。

## 4. TODO 1：实现 `code/citations.py` 的 `check_citations()`（约 25～35 分钟）

目的：找出缺引用或引用了不存在资料的问题。**只改这个函数**，保留已提供的提取和包装函数。

- 输入：`answer: str`，以及合法的 `ContextBundle`；其 text/chunks 来自已有 `build_context()`，编号为 1 到 `len(context.chunks)`。类型与上下文内部一致性视为前提；不额外校验 None 或错误类型。
- 输出：`list[str]`，消息必须与下面表格精确一致。
- 异常：合法输入不抛异常；待完成的 `NotImplementedError` 必须替换。无文件读写、网络或网关调用，不修改 `answer`、资料文字或片段列表。

| 条件 | 返回要求 |
|---|---|
| 没有提取到任何编号（包括空回答） | `["missing_citation"]` |
| 所有提取编号都在 1～实际发送块数之内 | `[]` |
| 有编号小于 1 或超过实际发送块数 | 每个未知整数返回 `"unknown_citation:N"`，N 为该整数 |
| 同一未知整数重复出现 | 只记一次，按各未知整数第一次出现的顺序 |
| 合法编号和未知编号混合 | 仍报告所有未知编号，不能因为存在一个合法编号就整体通过 |

没有要求每一块资料都必须被引用，顺序也不必递增。有两块资料但只引用 `[2]` 是合法的。

例如，两块上下文、回答 `回答。[99][2][99][0][2]` 的结果为：

```text
["unknown_citation:99", "unknown_citation:0"]
```

处理顺序：使用已提供函数获取编号；分清“没有编号”和“有编号但未知”；以本次发送块数为边界，依出现顺序核对并收集不重复的错误，返回完整列表。即使直接传入空上下文也遵守表格：回答 `[1]` 时返回 `unknown_citation:1`。正常问答的无资料分支由已提供的包装函数跳过检查。

本日采用严格、简单的“generated 文字应有引用”检查。即使模型在有资料时回答 `資料からは回答できません。`，也会报告 `missing_citation`，交给人工核查；这不代表该拒答内容一定错误。不要新增拒答例外或改提示词。

完成标准：这个文件中的 **16 项测试通过**（提取 3、核心 9、问答检查 3、无资料 1），包含重复、混合、编号 0、两位数和原资料不变。

```text
.\.venv\Scripts\python.exe -m pytest Week5/day33/tests/test_citations.py -q
```

## 5. TODO 2：独立写一个同主题边界测试（约 15～20 分钟）

只替换 `tests/test_day33_extra.py` 中的占位函数。目的：证明合法编号取决于实际发送资料，不取决于检索命中数。

先按此顺序构造两块，`chunk_index=0`、`start=0`、`end=len(text)`：

| 变量 | 来源 | 原文 |
|---|---|---|
| `long_chunk` | `long.txt` | `"返品" + "B" * 80` |
| `faq_chunk` | `faq.txt` | `"返品期限は30日"` |

设 `expected_context="[1] faq.txt (0:8)\n返品期限は30日"`。用问题 `"返品"`、`top_k=2`、`max_context_chars=len(expected_context)` 调用 `answer_question()`；替身为 `RecordingGateway("返品期限は30日です。[2][2][0]")`。再将结果传给 `review_qa_result()`。

这两块都命中且同分；第一块放不下，只有第二块实际发送，编号重新从 `[1]` 开始。

必须断言：

- 完整错误列表为 `["unknown_citation:2", "unknown_citation:0"]`，检查重复编号只出现一次及错误顺序。
- 原结果仍为 `generated`、answer 等于固定返回文字，网关恰好调用一次；错误不会改写答案或再次调用。
- 完整 `result.context.text == expected_context`、`result.context.chunks == [faq_chunk]`，且其中对象 `is faq_chunk`。
- 用 `json.loads()` 检查真正发送的完整输入为 `{"question": "返品", "context": expected_context}`，没有包含跳过的长块。需要自行补 `json` 导入。

无需重复实现 Day32 的全部输入不变测试，复制来的 52 项仍保留该契约。测试只删除占位、没有断言不能算完成。pytest 成功退出 0、断言失败退出 1。

## 6. 实现后验证与复盘（约 15～20 分钟）

仓库根目录运行：

```text
.\.venv\Scripts\python.exe -m pytest Week5/day33/tests -q
.\.venv\Scripts\python.exe -m Week5.day33.code.run_citation_demo
```

目标 **69 passed**；只完成核心函数时为 **68 passed / 1 failed**。演示已提供，不实现新 CLI 或 help。无参数、无输出文件；TODO 未实现时简短提示、退出 1；完成后退出 0，输出五行可解析的 UTF-8 JSON：

| case | status | citation_errors | gateway_calls |
|---|---|---|---|
| valid_id | generated | `[]` | 1 |
| unknown_id | generated | `["unknown_citation:99"]` | 1 |
| missing_id | generated | `["missing_citation"]` | 1 |
| wrong_content | generated | `[]` | 1 |
| no_context | no_context | `[]` | 0 |

`wrong_content` 故意返回“90日”并引用存在的 `[1]`。编号检查通过但内容与原文不符，需人工核查。无资料行的空错误列表表示跳过检查，不表示生成回答已通过。演示的五个返回都来自人为固定样例，不是真实模型证据。

在笔记填两题复盘、自报实际用时和难度，再交助手验收；不要求重跑历史所有日，也不用起止时间差替代实际用时。后续在已有问答链路接真实模型与人工核查时，继续保留编号检查的范围限制。

## 7. 助手建立验证（非学习者必做）

- Day32 必需业务代码和 52 项测试复制到当天目录，项目导入已改为 `Week5.day33`；复制后、增加练习前 **52 passed**。Day32 原目录复测 **52 passed**，历史实现和笔记不改。
- 初始当天实测 **56 passed / 13 failed**，失败均为本日两个 TODO。核心实现和独立测试保留给学习者；尚未记作完成，开始时间、自报用时和答案待填写。
- 后续参考契约、模块输出与环境检查结果写在当日笔记；助手的临时参考验证不算学习者完成。
- 临时进程参考验证 **69 passed**，五案例演示的原回答/来源/编号错误/调用次数及 UTF-8 均正确；参考实现未写入作业。磁盘占位演示退出 1，提示先完成函数，无 traceback。`pip check`、敏感模式、UTF-8、当天导入与本地链接检查通过，无共享变更，不重跑全仓。

## 8. 最终验收（2026-10-11）

- 学习者完成核心函数与独立测试，首次检查 **69 passed，无警告**。缺引用、编号范围、去重顺序和实际发送资料检查符合契约，独立测试完整覆盖任务单要求，不需修改核心逻辑。助手仅补中文注释、整理两处空白和移除未使用的 pytest 导入。
- 实际子进程演示退出 0，五行完整 UTF-8 JSON、原回答、来源、错误列表与调用次数正确；临时运行目录无输出文件、stderr 无 traceback。额外手动核对有资料拒答仍报告 missing_citation，以及合法/未知编号混合去重；pip check 通过。
- 两题复盘结论正确，第 2 题理由补准为“编号对应资料确实存在，但没有验证 90 日是否有原文依据”，原答保留；对话中已讲解提取与检查分工、请求 JSON 位置及合法编号来源，不追加问答。
- 实际用时自报 **1h**，反馈 **简单**、仍需讲解 **无**。没有真实模型调用，不把离线编号检查通过当成回答质量证据；下次以一个现有例子短复习编号存在与内容有据，再继续真实问答主线，不补交旧题。
