# Day 12 补充复习：替换函数了吗？取得对象就会分析吗？

这是学习者在原作业通过后主动要求的补充，参考 20～30 分钟。不追加原作业的验收门槛，不要求现在进入新框架。原作业自报 20min 和结束时间 2248 保留；本段实际用时若要记录，请另行自报，不从时间差推算。

## 先修准一句话

原复盘说“with 内 get_analyzer 被替换，离开后恢复”，对临时生效的范围理解正确。更准确地说：**FastAPI 在处理 Depends 时临时选择另一个函数；get_analyzer 的代码和名称绑定本身没有改变。**

因此，即使在 with 里面，直接写 `get_analyzer()` 仍然执行原函数。只有通过 FastAPI 处理请求，才会查询 dependency_overrides 中的对应关系。这与把 Python 模块中的某个函数直接 monkeypatch.setattr 成另一个函数不同；本题只改了一项字典内容。

## 第一段：先预测，再运行

已有脚本 review_flow.py 是助手提供的观察示例，不是新 TODO。先打开它，只看编号 1 和编号 2；细节不用一次读完。

同在 with 范围内：

1. `direct = get_analyzer()` 会拿到真实对象，还是 fake？
2. `client.post(...)` 让 FastAPI 处理请求后，响应会包含 CSV出力，还是固定のテスト結果？

两个调用入口不同，先在心里判断即可，不必写长答案。脚本里的 provider_calls 只记录提供对象的函数被调用的次数；fake.calls 仍记录 analyze 收到的文本，两者不是同一本记录。

根目录执行，PowerShell / CMD / Cmder 通用：

```text
.\.venv\Scripts\python.exe -m day12.review_flow
```

脚本使用 TestClient 在本机进程内运行，不启动新端口、不调用外部服务、不写文件；正常退出码为 0。开头出现已有依赖弃用警告不表示失败，以编号输出、断言结果和退出码判断。为了独立运行，脚本手动创建 monkeypatch 对象；with 内的用法就是已经看过的 context，不要求学习新的 fixture 设计。

## 第二段：昨天的长度检查为什么还能取得对象？

只看脚本编号 3，以及 Day 11 的这两处代码：

```python
analyzer: RuleBasedAnalyzer = Depends(get_analyzer)
```

以及路由函数体的第一步：

```python
check_text_length(request.text)
```

对当前这个有效 JSON、text 为字符串的请求，FastAPI 在执行路由函数体前处理依赖、取得 analyzer；进入函数体后，长度检查发现 2001 字符，抛出 413，后面的 invoke_analyzer 不执行。

因此，刚刚这个超长请求仍调用了 get_test_analyzer，但没有调用 fake.analyze。脚本累计值应为：提供对象 2 次，分析 1 次；不要误以为超长请求自己分析了 1 次，那个 1 来自前面的正常请求。

这就是昨天“超长时 calls 应为空”那题的含义：若使用全新的 fake，只发送一次超长请求，它的 calls 是 []。本示例在已有一次正常请求后再发超长请求，所以列表保留之前的一条，不再追加。

不把这个顺序推广成“所有请求校验都一定先于/晚于所有依赖”；今天只观察当前路由、当前有效字符串输入的长度拒绝路径。

## 第三段：确认恢复，再用一句话说明

脚本编号 4 离开 with，再发正常请求，结果恢复为 CSV出力，fake.calls 和 provider_calls 都不再增加。

本段只需在对话中说明两句话：

- 为什么在 with 内直接调用 get_analyzer() 仍得到真实对象？
- 为什么超长请求会取得 fake，却不会调用 fake.analyze？

如果仍有疑问，带着对应编号继续问；这比重新背昨天十道题更有针对性。

## 还有余力时的小练习（可选，不影响原作业完成）

在 test_day12.py 新增 test_oversized_request_keeps_existing_call_records，沿用已有临时替换框架，自己实现以下步骤：

1. 创建一个 FixedAnalyzer，以 INPUT_A 发一次正常请求，确认 200、完整 JSON 等于 expected.model_dump()。
2. 使用同一个 fake，再发送 text 为 `"あ" * 2001` 的请求，确认 413；detail 精确为 `{"code": "TEXT_TOO_LONG", "max_length": 2000, "actual_length": 2001}`。
3. 断言 fake.calls 精确为 `[INPUT_A]`，不是空列表，也不能出现超长字符串。

只改新测试，不改已经正确的 exercise.py 或 Day 11 路由。目的：既保证超长请求没被分析，也保证此前记录没有被清空。完成后本日测试数会从 5 增至 6，全仓从 109 增至 110；这些是可选练习的目标，不是当前实测结果。
