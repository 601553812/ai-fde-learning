# Day38 — 用固定问题集验证一次检索改善

状态：已完成学习与代码验收（2026-10-17），177 passed，无警告；自报1.5h、难度中，复盘原答与助手参考答案分别保留。唯一主题：**只更换检索算法，用相同问题、预期和预算比较前后结果**。下方TODO与初始失败为原作业契约和建立历史，当前结论见第9节。

已复制Day37必要Python模块与146项测试到本日，导入和monkeypatch路径更新为`Week6.day38`。新增练习前146 passed；旧检索、资料预算、证据检查、问答和HTTP行为均保留。历史目录不改，无新依赖；无需重学复制模块。本日不执行真实模型入口。

## 1. 开始顺序

工作目录：仓库根目录。以下单行命令适用于**PowerShell与CMD/Cmder**，使用根`.venv`的Python3.11。

1. 在[学习记录](./day38_notes.md)填写开始时间，无需提前回答概念题。
2. 先运行初始脚手架检查：

```text
.\.venv\Scripts\python.exe -m pytest Week6/day38/tests -q
```

初始实测**152 passed / 25 failed**，退出1：146项既有测试、5项已提供字符对辅助函数测试、1项空报告测试通过；其余来自两个新函数及独立测试的TODO占位。这是练习起点，不是旧行为回归。实现后不用还原初始状态。

3. 阅读第2～3节，再按此顺序看非测试代码：`code/eval_cases.py` → `code/bigram_retrieval.py` → `code/retrieval_compare.py` → `code/run_compare_demo.py`。
4. 依次完成第4～6节，只需修改两个函数所在文件和`tests/test_day38_extra.py`；最后运行、观察、填写复盘。

## 2. 一例短复习：今天到底检查什么

R1的人工预期是returns_faq.txt中的「返品期限は30日です。」。`check_evidence()`查的是：**预算后context.chunks中，有没有同来源且包含这句完整原文的片段**。今天仍然没有模型回答；hit_rate不是模型准确率。这段是对Day37概念的简短复习，不需补交旧题。

Day37的R4问题「パスワードを変更するには？」没有空格。旧`retrieve_chunks()`把整句当成一个词项；这句话不是原文「パスワードは設定画面から変更できます。」的连续子串，于是漏检。

今天尝试一个小改动：不要求整个词项都包含，而是数问题与原文共有多少种**相邻两个字符**。这叫字符bigram（本日称“字符对”）。

```text
パスワード → パス / スワ / ワー / ード
```

两个句子即使助词不同，仍可能共有这些文字。这个方法不理解“密码修改”的含义，也不认识同义词；它只是比整句子串匹配更细的文字匹配。得到改善也只能说明这些固定题的证据覆盖变化，不能推广为理解了所有日文。

为了让比较有意义，保持以下输入相同：三份资料、六个问题、source_name/quote预期、切块方式、top_k=2、max_chars=500。只更换检索算法。不要改R4问题，不把它的预期改成None，也不要按case_id、文件名或预期答案写特例。

## 3. 今天所需的最小知识与普通调用链

### 已提供的character_bigrams

`code/bigram_retrieval.py`已经实现字符对提取，不是TODO：

- 先`casefold()`统一大小写。
- 每次取`text[index:index + 2]`，长度为2的相邻字符。
- 两个字符都满足`isalnum()`才保留；这里包含日文汉字、假名、字母和数字。空白和标点使字符对断开，不先删除它们再拼接。
- 用set去重；单字符、空串或纯标点没有字符对，返回空set。

```python
from Week6.day38.code.bigram_retrieval import character_bigrams

# 小例子只解释辅助函数与集合；不是检索函数的完整实现。
assert character_bigrams("ABAB") == {"ab", "ba"}
assert character_bigrams("配送 日数。") == {"配送", "日数"}
assert character_bigrams("A!B") == set()  # 不跨标点造出ab

# &产生共同元素的新集合，不修改left或right。
left = {"ab", "bc"}
right = {"bc", "cd"}
assert left & right == {"bc"}
assert len(left & right) == 1
```

Java类比：set类似`HashSet<String>`，都按内容去重且没有用于排名的顺序；Python的`&`返回一个新集合。Java的`retainAll()`会修改接收者，不能直接当成同样的无修改操作。排名继续使用命中列表，不能根据set遍历顺序排名。

Chrome已核对[Python3.11官方集合说明](https://docs.python.org/3.11/library/stdtypes.html#set-types-set-frozenset)；今天只用去重、交集、len和已有稳定排序知识，不要求阅读整页。`score`是这一算法下共有的不同字符对数，不是概率，也不与旧算法的词项数直接比较大小。

### 先看函数如何被调用

```text
run_compare_demo.main()
  → evaluation_chunks() / evaluation_cases()：沿用相同资料和固定六题
  → compare_retrieval(chunks, cases)：每题执行下面两条链
      旧 retrieve_chunks(chunks, case.question, top_k)
         → build_context(hits, max_chars) → check_evidence(case, context)
      新 retrieve_bigrams(chunks, case.question, top_k)
         → build_context(hits, max_chars) → check_evidence(case, context)
      → classify_change(旧evidence_found, 新evidence_found)
  → summarize_evidence()：分别汇总旧/新证据结果
  → json.dumps：一次打印完整报告
```

`baseline`指旧方法的检查记录，`candidate`指新方法的检查记录；这两个名字在代码和报告中一致。两个检索器只接收chunks、question、top_k，完全看不到人工预期。后面的check_evidence才拿预期检查结果。

N1「返品 送料」即使命中返品相关资料，仍没有送料承担方的预期原句；N1/N2保持None，不纳入有答案问题的比例。今天没有调用LLM，也没有实际回答，报告不能证明发生了正确回答或合理拒答。

腾讯课程对应路线4.1“固定样例评测”的前后比较思想，必要内容已在本节解释，不增加读书报告。今天不学日文分词库、Embedding、向量库、BM25、语义评分、LLM-as-judge、Prompt调优、UI或Docker；Docker旧闸门仍未验证，不追加到今天。

## 4. TODO 1：实现字符对检索

文件：`code/bigram_retrieval.py`，函数`retrieve_bigrams(chunks, query, top_k)`。

- 目的：用更小的文字单位找资料，保留旧方法作前后比较。
- 输入：合法Chunk列表、str问题、int上限；不要求额外处理其他输入类型。
- 输出：新的`list[RetrievalHit]`；每项chunk必须是输入中的原对象。RetrievalHit直接来自`.retrieval`模块，已导入，不需配置`__init__.py`。
- 异常：先检查空/全空白query，抛`ValueError("invalid_query")`；再检查top_k<=0，抛`ValueError("invalid_top_k")`。这两种同时非法时先报invalid_query；空chunks也必须先校验参数。
- 合法但没有字符对的query（如「猫」或「! ?」）返回空列表，不抛invalid_query。不增加单字符回退规则。

处理步骤：校验参数 → 调辅助函数得到问题字符对 → 逐块得到原文字符对并算共有种数 → 只保留score>0的命中 → 按score降序稳定排序 → 最后截取top_k。

完成标准：

- score为问题字符对集合和该块text字符对集合的共同元素数；重复出现只计一次。
- 不匹配source_name；同分保持输入顺序，不按来源名重排。
- 不改变输入内容、顺序、对象身份，不改旧retrieve_chunks，不调用模型、不读写文件。
- 空chunks或没有共同字符对时返回[]。
- 固定R4返回account_help.txt原片段，score=5（パス、スワ、ワー、ード、変更）。这个值用于核对规则，不能硬编码。

```text
.\.venv\Scripts\python.exe -m pytest Week6/day38/tests/test_bigram_retrieval.py -q
```

## 5. TODO 2：逐例区分改善、退步和不评分

文件：`code/retrieval_compare.py`，函数`classify_change(before, after)`。只实现这个函数；报告组织函数已提供。

- 目的：不能只看总比例，必须能发现某一题从命中变漏检。
- 输入：同一道题两次检查的evidence_found，各为True/False/None；不是检索score，也不是模型回答。
- 输出：下表中的一个精确字符串；无新增异常。删除NotImplementedError占位，不修改外部状态。

| before | after | 返回字符串 |
|---|---|---|
| False | True | improved |
| True | False | regressed |
| True | True | unchanged |
| False | False | unchanged |
| 任意一边为None | 任意 | unscored |

处理顺序：先区分能否评分 → 再区分是否发生布尔值变化及其方向 → 返回字符串。两边值相同并不足以判unchanged，因为None/None应为unscored。合法输入不需要新增校验或异常信息。

```text
.\.venv\Scripts\python.exe -m pytest Week6/day38/tests/test_retrieval_compare.py -q
```

两个函数完成后，当天应只剩独立测试TODO失败；最终总目标177 passed。

## 6. TODO 3：独立验证改善何时消失

文件：`tests/test_day38_extra.py`，完成已命名测试，删除pytest.fail及不再需要的pytest导入。使用普通函数，不需要网络替身。

具体子模块导入（直接导入，不需修改包导出）：

```python
from dataclasses import asdict
from Week6.day38.code.eval_cases import evaluation_cases, evaluation_chunks
from Week6.day38.code.bigram_retrieval import retrieve_bigrams
from Week6.day38.code.retrieval import retrieve_chunks, RetrievalHit
from Week6.day38.code.context import build_context
from Week6.day38.code.retrieval_eval import check_evidence
from Week6.day38.code.retrieval_compare import classify_change
```

目的：新方法检索到原文后，只有证据实际进入预算后的资料，才算这道题改善。输入固定为R4，不改问题或预期。

操作顺序：

1. `case = evaluation_cases()[3]`，`chunks = evaluation_chunks()`。
2. 在检索前保存case完整asdict快照、各chunk的asdict快照，以及`originals = chunks.copy()`保留原对象。
3. 同一份chunks与case.question分别调用旧/新检索器，top_k均为2，得到old_hits/new_hits。
4. old_hits按500预算建立context并检查；同一份new_hits依次按500和1预算建立full/tiny并检查。三份检查记录可自行命名。
5. 两次调用classify_change：旧检查→full检查、旧检查→tiny检查；全部调用后断言。

必须验证的完整行为：

- old_hits为[]；全部调用后new_hits仍完整等于`[RetrievalHit(originals[2], 5)]`，其中chunk `is originals[2]`。
- full.chunks完整等于`[originals[2]]`且保留同一对象；tiny完整asdict等于`{"text": "", "chunks": []}`。
- 三份检查的evidence_found依次为False/True/False；每份case均`is case`，每份context均为相应传入的context对象。
- 两个classify_change返回字符串分别为improved/unchanged。
- 所有调用后，case与三个chunk的完整值及顺序与调用前快照一致；三个位置的chunk仍分别是原对象。

本题新增异常：无。通过以上断言和当天全部测试作为完成标准；不要求重写旧预算函数或制造模型回答。

## 7. 最后运行、观察与复盘

```text
.\.venv\Scripts\python.exe -m pytest Week6/day38/tests -q
.\.venv\Scripts\python.exe -m Week6.day38.code.run_compare_demo --help
.\.venv\Scripts\python.exe -m Week6.day38.code.run_compare_demo
```

预期：177 passed；help/正常演示退出0。正常输出为一行完整UTF-8 JSON，不生成文件、不需要密钥：

| 项目 | 旧方法 | 新方法 |
|---|---|---|
| R1/R2/R3/R4 | True/True/True/False | True/True/True/True |
| N1/N2 | None/None | None/None |
| 检索片段数，按R1～N2顺序 | 1/1/1/0/1/0 | 1/1/1/1/1/0 |
| total/evaluated/hits/misses/unscored | 6/4/3/1/2 | 6/4/4/0/2 |
| hit_rate | 0.75 | 1.0 |

- change依次unchanged/unchanged/unchanged/improved/unscored/unscored；gateway_calls=0；来源provided_synthetic_faq_v1。
- 未实现TODO时实际模块入口提示并退出1、无traceback；非法参数由argparse退出2。
- 同一批小样例从3/4变4/4是本次局部证据，不代表所有问题100%命中，更不代表模型回答100%正确。score单位不同，不能以“新分数更大”代替同一证据标准的比较。
- summary.hits是evidence_found=True的题数，与检索返回的片段数不同。check_evidence对照人工预设的source_name/quote与预算后的原片段；classify_change另比较同一题旧/新的evidence_found。复盘中的假设另明确题目与两个布尔输入，不将假设写成已发生的报告结果。
- 完成后在笔记填三题复盘、自报实际用时和难度，再请助手验收。开始学习不等于验收完成；今天先保留待完成状态。

## 8. 助手建立验证记录

- 初始152 passed / 25项预期TODO失败；临时进程参考177 passed，无警告。参考算法与独立断言没有保存到作业，不是学习者完成证据。
- 实际子进程help/TODO/非法参数退出0/1/2，无traceback；临时参考正常演示退出0、一行完整UTF-8报告、固定逐例结果、0.75→1.0及零调用正确，无输出文件。
- Python3.11.15、pip check通过；继承模块与测试除当天导入/展示日名外一致。材料建立验证与学习者执行记录分开，详见[笔记](./day38_notes.md)。

以上是建立时历史状态；当时两个核心函数和独立测试留给学习者，未完成学习、未提交推送。没有历史目录迁移、共享逻辑改动或新依赖，无需全仓重跑。当前完成结论如下。

## 9. 最终验收（2026-10-17）

- 学习者完成两个函数和独立预算测试，177 passed，无警告，pip check通过；去重计分、同分稳定排名后top_k、参数校验顺序、空输入、完整快照与原对象保留符合原契约。助手只补中文注释、空白与未使用导入，没有代写核心实现或独立断言。
- 实际子进程help/正常/非法参数退出0/0/2；完整一行UTF-8报告、六题结果、R4改善、0.75→1.0、零调用、无traceback或输出文件通过。这个1.0只表示4个有预期证据的问题在当前固定条件下全部找到证据；没有模型回答准确率证据。
- 原答、自报1.5h和难度中保留。复盘第3题比较层级不明及不相容总分假设已修正并记录为助手题目问题，参考答案不当作独立理解证据；不再要求补答。详细验收和列表身份订正见当天笔记。
- 下一日先用R4的500/1预算结果短复习，再沿固定评测与检索改善主线继续，不补交旧题；Docker旧闸门仍未验证。本日按默认规则提交同步GitHub，实际上传以远端核对为准。
