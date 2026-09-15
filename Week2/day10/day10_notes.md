# Day 10 学习记录

最终状态：已完成（2026-09-08）。下方保留原始答案、订正和分轮检查过程；最终澄清见文末，历史“待确认”不代表当前状态。

## 学习开始

- 开始时间：2155
- 环境确认：使用根目录 `.venv`，本日无需新增依赖：

开始时只填写以上内容。完成全部复盘后再填末尾结束时间；实际用时自行估计并排除中断。

## 本日学习目标（无需提前作答）

- 复习客户端与服务端：TestClient 仍返回 Response；JSON 解码、请求模型校验和业务校验发生在不同阶段。
- 看懂 strict 来自 URL query，text 来自 JSON body。
- 理解辅助函数中 raise HTTPException 如何终止本次处理，但不停止服务器。
- 自己实现两项错误策略，验证状态码、完整错误结构、字符长度边界和连续请求。

## 学习后复盘

1. Requests / TestClient 与 FastAPI 分别在请求的哪一侧？测试检查 Response 的哪些信息？
Requests属于客户端 请求侧 TestClient也是请求侧 FastAPI是服务端 测试检查Response的json内容和statuscode
2. `strict: bool = False` 和 `request: AnalyzeRequest` 的值分别从哪里来？为什么不能把 strict 塞进本题的 JSON body？
strict默认值 如果请求没有值就用本地默认值 request是必须从客户端也就是请求侧发来  把strict可以塞进去 但是判断的时候就需要先读JSON再判断哪个模式了 容易出问题
3. `raise HTTPException(...)` 与 `return {"detail": ...}` 有什么区别？从辅助函数 raise 后，路由剩余代码还会执行吗？
raise之后 出这个方法也不再往下执行了 但是return之后还是会继续执行 不会
4. 对同一个缺少验收条件的输入，默认模式和 strict 模式为什么返回不同状态码？各自有什么用途？
默认模式是正常处理了数据 但是严格模式则直接报错 默认模式可以用来做测试环境 但生产环境就用严格模式
5. JSON 损坏、text 为整数、业务缺项、文本超过上限分别在哪里被拒绝？什么情况下业务缺项并不被拒绝？
JSON损坏是FastAPI从response里接收JSON时拒绝 text为整数是JSON接收后创建model的时候拒绝 业务缺项则是我们做的validate_result 如果缺的不是我们限制的项就没事
6. 为什么长度 2000 可以通过、2001 不行？为什么不能用 UTF-8 字节长度代替 len(text)？本实现是否已经能防御超大 HTTP body？
因为我们业务就是这么设计的 你这个问题想问什么呢 不同编码字节长度不同 不能 因为本质还是把text全读到内存里后再判断是否超长
7. 今天新增了哪些断言？最终 Day 10 和回归 pytest 结果是什么？
没看出新增了什么 all passed
8. 手动验收记录：200 / 400 / 413 / 422、日文内容、错误后再次成功、服务日志：
没问题
9. 今天最不理解的点、下次需要复习的内容：
    assert response.json()["requirements"]["functions"] == []
    assert response.json()["requirements"]["acceptance_criteria"] == []
    assert response.json()["requirements"]["risks"] == []
    assert response.json()["requirements"]["questions"] == []
    assert response.json()["requirements"]["unknown"] == []  这个能简单化吗
10. 日语说明（3～5 句）：面向 API 调用者说明默认/严格模式、长度限制和错误信息。
システムについては、センター側にデフォルトモードと厳格モードをわけられた。
デフォルトモードについては、仕様に合わない入力があってもエラーせず、出力に記載しているモードです。
厳格モードについては、仕様に合わない入力があれば、エラーコード400、詳細情報に記載するモードです。
また、入力の文字列は、2000文字以内に制限されています。（2000もok）
## 错题本

出现典型错误后追加：错误写法、正确写法、原因、最小示例。

## 学习反馈

- 相比 Day 9，今天的量：偏少 / 合适 / 偏多，原因：合适
- 实际用时（排除中断，自行填写）：1.5h

## 验收补充（2026-09-08，原答案保留）

代码与真实 HTTP 验收通过，不需要返工。以下是验收者的解释，不替代学习者自行复述；请在本节后、结束时间前追加第 2～5 题的订正，再确认当天完成。

### 第 2～5 题需要明确的区别

- 第 2 题：本题 strict 来自 URL query，例如 `?strict=true`；没有提供才使用 False。request 模型来自 JSON body。**在当前接口契约下**，body 里塞 strict 会被 `AnalyzeRequest` 的 `extra="forbid"` 拒绝，返回 422，不是“读 JSON 比较容易出问题”。其他接口可以把模式设计成 body 字段，但那需要修改模型和接口契约，不能直接当成本题已有行为。
- 第 3 题：`return` 和 `raise` 都会离开当前函数。辅助函数 return 后，调用者回到调用点的下一句；raise 则向外传播异常，本题路由没有捕获它，因此后续路由语句不执行，由框架转为错误响应。不是“return 后当前函数剩余代码还会继续执行”。
- 第 4 题：默认/严格模式是**业务用途**的差别，不是测试/生产环境开关。生产系统的草稿诊断也可能需要默认模式，返回分析结果和缺项；严格检查需要不完整就拒绝。两种模式都应该在测试中覆盖，并且都仍拒绝不合法的请求结构和超长文本。
- 第 5 题：服务端收到的是 **request body**，不是 response。损坏 JSON 在解码时拒绝；text 整数在请求模型校验时拒绝；`validate_result()` 本身只返回缺项列表，不拒绝请求；`check_business_errors()` 才在 strict=True 且有缺项时抛 400。strict=False 时，即使缺少功能或验收条件，也返回 200 和缺项列表。超长文本由 `check_text_length()` 在 parser 之前抛 413。

### 第 6、7 题：提问目的补充

“因为业务这样设计”对第 6 题的第一问是正确回答。原题问法不够准确，本来应问：把 `>` 误写成 `>=` 会错误拒绝哪一个输入？2000 与 2001 的测试分别抓什么问题？目的是边界验证，不是追问为什么选择 2000 这个业务数字。

关于编码，更具体地说：UTF-8 下，一个日文字符通常需要多个字节；本题约束 `len(text)` 计算的 Unicode 码点数，不能拿字节数代替。你已经正确指出完整 body 先进入内存，因此这不是超大 HTTP body 防护。

第 7 题本应问“你补完的三项测试分别防止哪种错误”：单缺项防止把错误列表写死为两个缺项；空白输入验证字符串非空不等于业务完整；连续两次请求验证本次错误不会阻止下一次成功，也不污染新结果。不是要求你另发明一种 assert 语法。

### 第 9 题：五条断言可以合成一次完整字典比较

```python
assert response.json()["requirements"] == {
    "functions": [],
    "acceptance_criteria": [],
    "risks": [],
    "questions": [],
    "unknown": [],
}
```

它仍检查全部五个字段，还会拒绝多余字段；字典比较不要求键的排列顺序相同。这里没有替你改动测试代码，你现在的五条断言也正确。

只写 `all(value == [] for value in requirements.values())` 不完全等价：缺少字段乃至空 dict 也可能通过。当前固定 Schema 的练习优先显式比较整个 dict，不为省行数削弱验证。

### 日语说明的准确性补充

原文的大方向已表达出两种模式和长度限制，但「仕様に合わない入力があってもエラーせず」范围过宽：默认模式只保留业务缺项为结果，不是放过所有不合规输入。可对照下面的说明，原文保留：

> この API では、デフォルトモードと厳格モードを選択できます。
> デフォルトモードでは、機能や受入条件が不足していても解析結果に不足内容を含めて返します。
> 厳格モードでは、これらの不足がある場合に HTTP 400 と詳細情報を返します。
> どちらのモードでも入力形式の不正は HTTP 422、2000 文字を超える要件文は HTTP 413 となります。

## 错题本补充：终端中已修正的错误

只记录本项目 Day 10 的相关输出，不保存原始日志和本机路径。以下具体错误现已修正，不是待修代码清单。

1. **detail 套了两层（多轮重复）**：日志响应出现 `{"detail": {"detail": {...}}}`，导致完整 body 比较失败。最小错误示例是 `HTTPException(status_code=400, detail={"detail": {"code": "X"}})`；正确示例是 `HTTPException(status_code=400, detail={"code": "X"})`。框架会提供最外层 detail。示例对应机制，不能仅凭日志还原当时每个变量的赋值。
2. **set 不能作为本题 JSON body（多轮重复）**：日志中的 `json={"機能: 登録"}` 和 `json={" \n "}` 是 set，不是 dict；客户端 JSON 序列化时报 `Object of type set is not JSON serializable`，请求还未进入路由。正确最小示例为 `json={"text": "機能: 登録"}`，键值之间有冒号。
3. **成功与错误响应字段混用（多轮重复）**：400 body 没有顶层 requirements 或 validation_errors，错误列表在 `response.json()["detail"]["errors"]`；200 的业务缺项列表才是 `response.json()["validation_errors"]`。日志先后出现 requirements、validation_error、validation_errors、errors 的 KeyError，不能只靠给字段改名猜结构。
4. **遍历 dict 拿到 key，而非 value**：日志中的 `assert requirement == []` 实际比较 `'functions' == []`；后续 `requirement[Any]` 对字符串使用了类型标注对象作为索引，出现 `string indices must be integers`。最小错误示例：`for item in {"functions": []}: assert item == []`；正确遍历值用 `.values()`，或直接采用上方完整字典断言。`Any` 是类型标注用途，不是任意索引的通配符。
5. **精确字符串拼写**：`validation_error` 少了结尾 s；`"REQUIREMENT_INCOMPLETE "` 多了尾随空格。正确为 `validation_errors` 和 `"REQUIREMENT_INCOMPLETE"`。字典 key 与错误 code 都要按契约精确匹配，不通过对实际结果 strip 来掩盖错误。

## 学习过程与代码验收结果

- 本日相关日志有 13 轮完整 pytest 结果：`13 passed/4 failed → 43 passed/4 failed → 13 passed/4 failed → 43 passed/4 failed → 14 passed/3 failed → 15 passed/2 failed → 15 passed/2 failed → 15 passed/2 failed → 15 passed/2 failed → 15 passed/2 failed → 16 passed/1 failed → 17 passed → 47 passed`。前 12 轮中的第 2、4 轮还运行了历史测试；第 12 轮首次全通过，第 13 轮回归确认。全部失败轮后续标记为退出码 1，最后两轮为 0。
- 前两轮中的三项 TODO 主动失败表示测试尚未编写，不是三个独立概念错误。终端重绘残留及没有完整结果的命令不计入上述轮数；日志不能证明编辑器内的修改过程和当时思路。正常探索次数不用于惩罚性评价。
- 学习者日志记录了 health 200、默认分析 200、严格缺项 400、随后正常 200、请求类型错误 422、超长 413，以及服务关闭和下一条退出码 0。未在该段日志看到 docs 操作证据；验收者独立验证了 docs HTML 和 OpenAPI，不将自己的验证冒称为学习者操作。
- 独立自动验证：Day 10 `17 passed`，Day 6～10 `47 passed`，全仓 `88 passed`，`pip check` 通过；两条已有间接依赖弃用警告未屏蔽。Uvicorn 帮助正常。
- 独立真实 HTTP 验证：默认和严格模式、200/400/413/422/405、错误后再次成功、完整日文 UTF-8 输出、2000 字符允许、2001/2017 字符拒绝、body/query 错误、docs HTML/OpenAPI 均通过；临时目录未生成文件，访问日志无 traceback，临时验收服务已停止。源码调用链未发现外部 API 调用。
- 当前代码没有功能性阻塞。小型维护建议（不阻塞本日代码验收）：错误 body 的 max_length 可引用 `MAX_TEXT_LENGTH` 避免重复常量；末尾 pass 和未使用的 Any import 可在后续整理时去掉。不在本次检查中擅自改写你的实现。
- 实际用时按自报 `1.5h` 记录，学习量反馈“合适”，后续先保持该量。结束时间 `0003` 不改写、不根据日志估算。只待复盘第 2～5 题订正确认后完成整日验收和 GitHub 上传。

## 学习者订正（已填写，以下保留原文）

在此用自己的话补充第 2～5 题即可，不需要重做代码或增加练习。
2. `strict: bool = False` 和 `request: AnalyzeRequest` 的值分别从哪里来？为什么不能把 strict 塞进本题的 JSON body？
strict　从url query来 把strict可以塞进去 但是判断的时候就需要先读JSON再判断哪个模式了 容易出问题 当前实现不能塞进去的原因是逻辑没有实现 塞进去会返回422
3. `raise HTTPException(...)` 与 `return {"detail": ...}` 有什么区别？从辅助函数 raise 后，路由剩余代码还会执行吗？
raise之后 这个方法不再往下执行 这个方法调用的位置也不会继续执行 而是直接抛出错误 但是return之后当前方法会返回 但是调用的位置还是会继续执行 不会
4. 对同一个缺少验收条件的输入，默认模式和 strict 模式为什么返回不同状态码？各自有什么用途？
根据返回内容的需求 用途而选择需要的模式
5. JSON 损坏、text 为整数、业务缺项、文本超过上限分别在哪里被拒绝？什么情况下业务缺项并不被拒绝？
JSON损坏是FastAPI从response里接收JSON时拒绝 text为整数是JSON接收后创建model的时候拒绝 业务缺项则是我们做的validate_result返回列表 然后通过check_business_errors拒绝 如果缺的不是我们限制的项就没事

assert response.json()["requirements"] == {
    "functions": [],
    "acceptance_criteria": [],
    "risks": [],
    "questions": [],
    "unknown": [],
}
针对这个测试方法 response.json()["requirements"]本质不是一个list吗 为什么不能通过循环这个list 断言其中每一个元素都是空来测试呢
## 第二次复查与新增答疑（2026-09-08）

- 全仓复测 `88 passed`，已有两条依赖警告不影响结果。当前实现与前次代码验收一致，不要求重做代码；相关 Cmder 日志的大小和修改时间未变，沿用前次过程分析。
- 第 3、4 题的订正已到位，不需再重写。第 2 题已说明 query 与 422；更准确的原因是模型只允许 text，并用 `extra="forbid"` 拒绝额外字段，而不只是“相关逻辑没有实现”。
- 第 5 题已正确区分 validate_result 返回列表与 check_business_errors 决定拒绝，但仍漏了 strict=False 的情况。实际验证：相同 `{"text": "機能: 登録"}` 在 strict=false 时返回 200 和缺少验收条件的列表，在 strict=true 时返回 400/detail/errors。还需确认的只有这一业务开关条件，不必再次改写整段复盘。服务端解码的是 request body，不是 response。

关于新增问题：**requirements 是 dict，不是 list；dict 中的每个分类值才是 list。** 与 Java 对照，它类似 `Map<String, List<String>>`，不是 `List<List<String>>`。

实测结果：

```python
requirements = response.json()["requirements"]
type(requirements)                 # dict
type(requirements["functions"])    # list
```

可以循环，区别在于循环什么：

```python
for name in requirements:
    print(name)  # functions、acceptance_criteria 等字段名，不是 []

for items in requirements.values():
    assert items == []  # 遍历每个分类对应的列表
```

第二种写法确实验证了“现有分类的值都是空列表”。但如果接口漏返回了字段，甚至返回 `{}`，这个循环也可能通过；空 dict 会执行零次断言。因此想保持原测试完整性，还要验证字段集合正好包含那五个字段，或者直接使用上一节的整个 dict 比较。能用循环，不代表单独一个循环已经验证了全部响应契约。

当前只待确认第 5 题的默认模式条件，尚未做完成提交或 GitHub 推送；学习者的时长和结束时间保持原值。

## 最终澄清与完成确认（2026-09-08）

学习者在对话中补充：“我说反了 我以为是strict=true”。此前“400，缺少信息放在 detail”的回答按 strict=true 理解是对应的；该次回答按学习者澄清记录为看反模式，不继续要求重写复盘。

最终对照（缺少功能或验收条件、请求结构合法且长度未超限时）：

- strict=False：200，缺项在顶层 validation_errors，仍返回完整分析结构。
- strict=True：400，错误 code 和缺项列表在 detail 内，其中列表为 detail.errors。

复盘订正与澄清已确认，Day 10 完成。最后一次全仓复测为 `88 passed`，`pip check` 通过；没有修改业务实现，沿用本日真实 HTTP 验证和学习过程分析。提交前只清理测试文件末尾多余空行，原答案和订正全部保留。

实际用时仍为学习者自报的 1.5 小时，结束时间仍是 0003；后续保持本日学习量，次日简短复习 dict/list 与 strict 两种模式，不追加本日练习。

- 结束时间：0003
