# Day 9 学习记录

## 学习开始

- 开始时间：2340
- 环境确认：使用根目录 `.venv`，能够导入 FastAPI：
可以
开始时只填写以上内容。实际学习用时以你自报为准，不按日志跨度计算。

## 本日学习目标（无需提前作答）

- 看懂 `HTTP 请求 → AnalyzeRequest → 路由函数 → 旧解析器 → AnalysisOutput → HTTP 响应`。
- 区分 JSON 解码、请求 Schema 校验和需求内容的业务校验。
- 能从 `/docs` 发送一次请求，并用 TestClient 验证同一接口。

## 学习后复盘

- 实际用时（排除中断时间，估计也可以）：1h左右

1. Day 7 的 Requests 与 Day 9 的 FastAPI 分别扮演什么角色？
Requests只是发送请求 FastAPI是接受到请求的时候 根据请求的url来走不同的方法
2. `@app.post(...)` 与 `request: AnalyzeRequest` 分别告诉 FastAPI 什么？
post告诉FastAPI收到什么url的请求时 需要走这个方法 这个方法返回什么类型 request告诉FastAPI 这个方法需要传入的参数如何判断是否合法
3. `{"text": 123}` 与 `{"text": "備考: 対象外"}` 为什么一个返回 422，另一个返回 200？
因为123是int 不是str
4. HTTP JSON body 进入路由前，经过了哪些转换？为什么不需要自己调用 `request.json()`？
使用 Pydantic 校验 AnalyzeRequest
5. 为什么路由直接返回 `AnalysisOutput`，不先调用 `model_dump_json()`？
FastAPI自动做了
6. TestClient 是否需要提前启动 Uvicorn？今天的测试为什么不需要 FakeResponse？
不需要 因为有了FastAPI 我们已经不关心Request返回的response了 直接用json转成的dict等形式就行了
7. 完成了哪些 TODO？最终 pytest 结果是什么？
全完成 all passed
8. 手动验收：`/health`、`/docs`、POST 正常路径、422 错误路径分别是什么结果？
全成功 记录在cmder log里了
9. 今天最不理解的一个点：
没什么不理解的
10. 明天需要复习的内容：
没什么
11. 日语说明（3～5 句，向同事说明 API 的输入、输出和两类校验）：
FastAPIフレームワークを利用して、リクエスト前のデータ検証、リクエスト送信、レスポンス受信、レスポンスデータ検証をFastAPIより実現する。
データ検証のスキーマ、models.pyに記載してください。
センター側の実装について、リクエスト対象urlをメソードのコメント形で記載する。
## 错题本

出现典型错误后追加：错误写法、正确写法、原因、最小示例。

### 验收补充：JSON 层级、字段名和类型（原答案保留）

日志中 `test_analyze_uses_another_input` 与 `test_analyze_preserves_questions_and_unknown_lines` 曾在测试断言处失败；当前代码已经修正，以下不是待修复问题。

1. 重复出现的层级错误：`response.json()["functions"]`、`response.json()["risks"]` 会触发 `KeyError`。这两个字段在 `requirements` 内，不在顶层；正确访问为 `response.json()["requirements"]["functions"]` 和 `response.json()["requirements"]["risks"]`。
2. 类型错误：`assert response.json()["schema_version"] == ["1.0"]` 把版本期望写成列表；实际契约是字符串，应为 `== "1.0"`。
3. 字段名错误：`["unknown "]` 末尾多了空格，与 `"unknown"` 不是同一个 key；应为 `["requirements"]["unknown"]`。

最小示例：先看结构，再写访问路径和期望类型。

```python
body = {"schema_version": "1.0", "requirements": {"functions": ["登録"], "risks": [], "unknown": []}}
assert body["schema_version"] == "1.0"          # str，不是 list
assert body["requirements"]["functions"] == ["登録"]
assert body["requirements"]["risks"] == []
assert body["requirements"]["unknown"] == []   # key 中没有尾随空格
```

## 验收补充：概念订正（2026-09-07）

以下是验收者的补充，不改写上方学习者原答案，也不把补充视为学习者已独立复述的证据。

- 第 1、11 题：Requests 是客户端库，发送请求并接收响应；FastAPI 是本题的服务端框架，接收请求、校验数据、调用处理函数并生成响应。FastAPI 本身不替你向外部服务发送请求。
- 第 2、11 题：路由由 **HTTP 方法 + 路径** 决定；`@app.post(...)` 是可执行的装饰器，不是注释。`response_model=AnalysisOutput` 声明本题的响应契约，不是写了 `post` 就自动指定返回类型。可以类比 Java Web 的路由注解用途，但执行机制不完全相同。
- 第 3、4 题：请求 body 先进行 JSON 解码，得到 Python 数据；再由 Pydantic 校验并构造 `AnalyzeRequest`；最后路由调用业务校验。`{"text": 123}` 能通过 JSON 解码，但不符合字符串字段规则，返回 422；`{"text": "備考: 対象外"}` 符合请求模型，所以能完成分析，返回 200，并在 `validation_errors` 中列出缺少功能和验收条件。
- 第 6 题：TestClient 在进程内调用应用，不需要预先启动 Uvicorn；但 `client.post(...)` 仍返回 HTTPX Response，需要检查 `response.status_code` 和 `response.json()`。今天不用 FakeResponse，是因为路由只调用本地纯函数，没有外部 HTTP 依赖。以后路由调用外部 LLM/API 时，测试仍可能需要替换该依赖；有 FastAPI 不等于不再需要测试替身。

日语说明参考订正（保留原文供对照）：

> この API は、JSON の text フィールドで要件文を受け取り、機能・受入条件・リスクなどの解析結果を JSON で返します。
> FastAPI はリクエストを受信し、Pydantic のモデルに基づいて入力を検証します。
> 入力形式が不正な場合は HTTP 422 を返し、形式が正しくても要件が不足している場合は HTTP 200 の解析結果に不足内容を含めます。
> HTTP メソッドとパスをデコレータで処理関数に関連付け、TestClient でステータスコードとレスポンス内容を確認します。

## 学习过程与最终验收

只分析本日相关 Cmder 输出，不保存原始日志或本机路径。终端重绘会混入未最终执行的命令文字，因此以完整测试结果和后续 `CMD_META` 的退出码为依据，不把无结果的重绘算作额外测试执行。

| 有完整结果的执行顺序 | 结果 | 错误或结论 |
|---|---|---|
| 1 | Day 9：8 passed，2 failed | 两项自写测试均为顶层访问 `functions` 导致 KeyError |
| 2 | Day 6～9：28 passed，2 failed | 相同两项、相同层级错误再次出现 |
| 3 | 8 passed，2 failed | 版本字符串与列表比较；`unknown ` 多余空格 |
| 4 | Day 9：9 passed，1 failed | 顶层访问 `risks` 导致 KeyError |
| 5 | Day 9：10 passed | 本日测试全部通过，后续标记退出码为 0 |
| 6 | Day 6～9：30 passed | 回归通过，后续标记退出码为 0 |

- 两项测试的失败数变化为 `2 → 2 → 2 → 1 → 0`；第 5 次有完整结果的执行首次全部通过，之后又做了合并回归。这些是正常的编写、运行和修正过程，不代表当天学习失败。日志不能证明编辑器中每次具体修改或当时思路。
- 学习者日志有 `/docs`、`/openapi.json`、`/health` 的 200，以及 POST 正常 200、错误 422。curl 在收到 422 时仍记录进程退出码 0，说明要检查 HTTP 状态码，不能只看终端退出码。日志末尾的服务会话没有后续完成标记，不据此声称学习者已经停止服务。
- 验收者独立复测：Day 6～9 `30 passed`（含 Day 9 全部 10 项）；`pip check` 通过。两条已有间接依赖弃用警告不影响结果，未屏蔽或扩大到依赖迁移。
- 提交前全仓回归 `71 passed`，Uvicorn CLI 帮助正常退出；学习文件 UTF-8、JSON 样例和敏感信息扫描通过。
- 独立启动临时 Uvicorn 服务验证：`/health`、`/docs` HTML、OpenAPI、日文 UTF-8 正常响应、请求类型错误 422、损坏 JSON 422、业务缺项 200、错误方法 405 均通过；正常路径无 traceback，临时工作目录未生成输出文件。临时验收服务已停止；源码调用链未发现外部 API 调用。
- 本日四项 TODO 和接口行为验收通过；复盘已补充订正。下次先复述客户端/服务端、TestClient 的 Response，以及 JSON 解码/请求校验/业务校验的区别，再进入新任务。
- 教学反馈：本日内容偏少，后续在同一主主题下适度增加一项独立实现和测试的相关功能或边界场景，按反馈调节；不追溯加题。结束时间移到本文件最后一行，实际用时保留学习者自报的约 1 小时。

- 结束时间：0130
