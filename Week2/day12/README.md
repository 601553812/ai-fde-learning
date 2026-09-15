# Day 12 — 用一个案例捋清分析器替换

日期：2026-09-10（日本时间）

状态：原作业已完成（2026-09-10 验收通过）。自报 20min，Day 12 为 5 passed，Day 11～12 为 21 passed，全仓 109 passed，pip check 通过。

学习者主动要求增加一点内容，已另附 [Day 11 定向复习](./review_day11.md) 和可运行观察脚本；原作业不重开、不追加验收门槛，补充学习进度单独记录。下方保留原始任务说明及脚手架历史结果。

## 今天是否复习，是否学新内容？

需要复习，但只围绕昨天的恢复测试，不重做昨天所有题。不引入新库、新 API 业务或新的框架概念。新增练习是让同一个替身处理两次不同请求，并验证原文、顺序和结果；不是再堆一组状态码题。

参考约 90 分钟，讲解和消化也算学习，不为凑时长加题。今天只修改 exercise.py 中的一个方法、test_day12.py 中的一项测试，以及学习记录。继续使用 Day 11 已验证的 API，不创建新的服务或改历史代码。

## 第一步：已经理解的内容，快速回看即可

`analyzer = get_analyzer()` 得到负责分析的对象；`output = analyzer.analyze(text)` 才得到 AnalysisOutput。output.requirements 是 RequirementData，里面有多个字符串列表，output.validation_errors 是另一个字符串列表。schema_version 固定为 1.0。

今天已通过口头梳理和类图确认这层关系，不重复追问。

## 第二步：先看非测试代码，再读一个恢复测试

先读 exercise.py，再读 test_day12.py 的 test_override_scope_restores_real_service；如果卡住，只带来当前这一行，不需要一次理解完整文件。

### 1. 替身只是一个普通对象

FixedAnalyzer 继承 RuleBasedAnalyzer，并重写 analyze。Java 类比是子类覆盖同名方法，不需要 Spring。真实分析器按规则解析文本；这个替身不解析，始终返回预先准备的结果。

构造函数已经给出：self.output 保存结果，self.calls 是这个对象自己的空列表。构造对象不等于执行 analyze。后续每调用一次 analyze，才记录一次收到的文本。

只需用到你学过的列表追加和 return。例如下面是另一个业务的小例子，不是作业答案：

```python
visited = []
visited.append("first")
visited.append("second")
# visited 现在是 ["first", "second"]，第二次 append 不会清空第一条。
```

### 2. 提供对象的函数，不负责分析

恢复测试中已经提供：

```python
def get_test_analyzer():
    return fake
```

它每次返回外面已经创建的同一个 fake，不在这里分析文本，也不每次重新创建替身。今天用这种具名函数，不要求同时阅读 lambda。

FastAPI 原本按 Depends(get_analyzer) 取得真实对象。测试临时告诉它：“这段时间改用 get_test_analyzer 取得对象。”处理请求的路由函数不变，只是 analyzer 参数收到的对象变了。

### 3. 替换规则与临时范围

```python
with monkeypatch.context() as patch:
    patch.setitem(app.dependency_overrides, get_analyzer, get_test_analyzer)
    # 在这个缩进范围内发送请求，FastAPI 会使用 get_test_analyzer。
# 离开范围后，patch 记录的修改被撤销。
```

dependency_overrides 是字典。key 是原函数 get_analyzer，value 是替代函数 get_test_analyzer，两者都不加调用括号。不是改路由，也不是改写 get_analyzer 本身；普通代码直接调用 get_analyzer() 仍然执行原函数。这套替换规则由 FastAPI 在处理依赖时查询。

with 的清理逻辑已提供，不需要自己设计；original 只是原字典的副本，assert 只检查是否恢复，真正撤销修改的是离开 context 时的清理。

### 4. 不要把返回的数据和 HTTP 响应混在一起

- fake：FixedAnalyzer 对象，可查看 fake.calls。
- expected：AnalysisOutput，包含预设结果。
- response：client.post 返回的 HTTP Response，可查看 status_code、调用 json()。
- response.json()：响应解码后的 dict；expected.model_dump()：模型转换后的 dict，可以比较完整内容。

常见错误是对 response 访问 calls；calls 是我们在替身上定义的属性，不属于 HTTP Response。

官方依据已筛选为以上最小内容，无需通读：[FastAPI 依赖覆盖的字典规则](https://fastapi.tiangolo.com/advanced/testing-dependencies/#use-the-appdependency_overrides-attribute)、[pytest monkeypatch 的临时修改与恢复](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)。

## TODO 1：实现替身的分析方法

文件：exercise.py，FixedAnalyzer.analyze。

- 输入：str text；self.output 和 self.calls 已由构造函数准备好。
- 步骤：把收到的原始 text 追加到 self.calls；返回 self.output。
- 输出：AnalysisOutput 对象，不是 dict、JSON 字符串或 HTTP Response。
- 不解析、不 strip、不清空旧记录、不新建分析器，不额外调用真实分析器。本题不增加异常处理。
- 删除 NotImplementedError 占位。完成条件：直接调用能得到预设结果，calls 记录原文；已提供的恢复测试也通过。

## TODO 2：同一替身处理连续两次请求

文件：test_day12.py，test_two_requests_keep_both_inputs。准备对象和临时替换的代码均已提供，保留这些代码；替换 pytest.fail 占位。

1. 在 with 范围内，用 client.post 向 ENDPOINT 发第一个请求，JSON body 为 `{"text": INPUT_A}`，保存返回的 Response。
2. 再向同一路径发第二个请求，body 为 `{"text": INPUT_B}`，另外保存 Response。不用列表循环，先写清楚两次调用。
3. 分别检查两次状态码为 200，两次完整 response.json() 都等于 expected.model_dump()。
4. 检查 fake.calls 精确等于 `[INPUT_A, INPUT_B]`，既保留第一条，也记录第二条，顺序和空格换行不变。

作用：两次输入不同，但替身固定返回相同的结果。检查 HTTP 结果确认路由用了替身；检查 calls 确认两次文本都正确传入。只检查长度等于 2，或只检查最后一次输入，不算覆盖原文和顺序。

不新增业务异常或退出码。测试正常通过时 pytest 退出码为 0；有未完成占位或断言失败时为 1。

## 怎么运行

根目录执行，PowerShell / CMD / Cmder 通用，固定使用根 .venv。

平时只运行今天的测试：

```text
.\.venv\Scripts\python.exe -m pytest Week2/day12/test_day12.py -q --tb=short
```

准备验收时再运行昨天和今天的回归，不要求每次两条都运行：

```text
.\.venv\Scripts\python.exe -m pytest Week2/day11/test_day11.py Week2/day12/test_day12.py -q --tb=short
```

初始预期：Day 12 为 2 passed、3 failed。两个失败来自 analyze 的 NotImplementedError，占位测试自己还会失败一次，这是练习未完成，不是环境损坏。完成 TODO 1 后预期 4 passed、1 failed；完成 TODO 2 后目标为 5 passed。昨天加今天目标 21 passed，全仓目标 109 passed。不得删除提供的断言或使用 skip/xfail 隐藏失败。

脚手架实测（2026-09-10）：本日 2 passed / 3 failed，全仓 106 passed / 3 failed；三项失败全部对应本日占位，历史 104 项保持通过。UTF-8、敏感信息扫描和差异空白检查通过；没有修改历史代码或安装新依赖。脚手架目前仅保存在本地，最终验收后再提交上传。

## 今天的顺序和完成标准

1. 填开始时间；类图仅快速回看（约 5 分钟）。
2. 分段读上面的最小知识和已有恢复测试，疑问逐行讲（约 25 分钟）。
3. 完成 TODO 1 并检查已有测试（约 20 分钟）。
4. 完成 TODO 2，关注两个不同输入及 calls（约 25 分钟）。
5. 只复盘三题，记录实际用时，最后填结束时间（约 10～15 分钟）。

验收不仅看 5 项通过，还会阅读两个 TODO 的实际实现和断言，确认不是写死结果或绕开请求；检查恢复后的真实结果、旧 Day 11 行为、无外部请求和无新增文件输出。今天没有新增 HTTP 路由或 CLI，无需重新练习启动两个服务器；这些步骤不是今天的作业。

原作业已经按上述标准验收通过，复盘和进度已更新；最终同步结果在完成回复中报告。补充观察脚本也已在临时工作目录验证正常/超长/恢复路径，退出码 0、UTF-8 正确且无输出文件。补充复习是否理解、是否完成可选测试，后续另外确认。

## 今天不需要学习

新的状态码、503 的全部分支、LLM SDK、密钥、异步、数据库、Spring、复杂依赖容器、装饰器实现原理、lambda 的其他用法、自己设计 fixture、参数化测试。昨天的十题不补做，也不要求新增日语作文。
