# Day 7 学习记录

## 学习开始

- 开始时间：20.15
- 环境确认：根目录 `.venv` 能否导入 `requests`：
可以
开始时只填写以上两项。下面的问题学完后再回答。

## 完成后复盘

- 结束时间：0.10
- 实际用时：估计2-3h

1. `class RequirementApiError(RuntimeError)` 中，括号里的 `RuntimeError` 表示什么？
表示定义的这个error的父类是runtimeError
2. `-> RequirementData` 表示什么？Python 是否会仅凭它自动检查返回值？
这个方法返回值的类型是RequirementData,不会检查
3. `requests.get()`、`Response`、`response.json()` 三者分别是什么？
requests.get是发送请求到服务器 ~~response是服务器处理完请求回复的内容 response.json是把回复的内容转成json格式~~
Response 是完整的 HTTP 响应对象；response.json() 把响应中的 JSON body 解析成 Python 的 dict/list，不是“转成 JSON”。
4. 为什么 HTTP 请求要显式设置 `timeout`？
避免写代码的时候忘记设置timeout导致这个request一直卡死在这
5. 为什么要在 `response.json()` 之前调用 `raise_for_status()`？
~~先模拟服务器回复信息后再模拟信息转json~~
raise_for_status() 检查 HTTP 状态码；遇到 4xx/5xx 会先抛出异常，防止把错误响应当成正常 JSON 继续处理。
6. JSON 能成功解析以后，为什么还需要 `RequirementData.model_validate()`？
需要检查里面的信息是否合法 是否有非预期的内容
7. 为什么对外统一抛出 `RequirementApiError`，同时又要用 `raise ... from exc` 保留原因？
~~外部可以根据错误信息处理 或者记录日志 方便以后程序维护~~
统一抛出 RequirementApiError，让调用方只处理一种项目异常；raise ... from exc 则保留底层超时、HTTP、JSON 或 Schema 错误，方便日志和调查。
8. pytest 最终结果：
all passed
9. 今天完成了哪些 TODO？
123456
10. 今天最不理解的一个点：
还是python的基础语法很多都不熟悉 不熟练 看代码速度很慢
11. 明天需要复习的内容：
根据我对你的提问 分析一下我的弱项
12. 日语说明（3～5 句，向客户说明 HTTP 获取、Schema 校验和失败处理）：
HTTPよりセンターから情報をダウンロードする機能を実装する。
リクエストする際に発生するエラー状況を事前予想し、それぞれを区別して処理する。
センターから取得した情報を検証して、規定のスキーマと合わない場合に対して、エラーを記録する。