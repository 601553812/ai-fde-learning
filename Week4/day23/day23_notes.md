# Day23 学习记录 — 批处理 HTTP 接口

## 学习开始

- 开始时间：1557
- 环境确认：原项目根目录，根 .venv Python 3.11；先按 README 第 0 节运行初始测试。

## 学习目标（无需提前作答）

- 沿 request → Task → run_batch → make_response 解释调用顺序。
- 区分 HTTP 响应状态与每个任务的调用结果。
- 用真实 HTTP 入口验证重复编号与零调用边界。

## 执行记录（学习后填写）

- 初始测试：
- 实现后本日 / 全仓测试：
- 样例真实本地 HTTP 的状态与汇总：
- 重复编号 / 非法上限 / 空批次的 HTTP 结果：

## 学习后复盘

1. test_api.py 的 test_mixed_batch_http_200_keeps_failed_row 中，A 成功、B 返回上游 403、C 先 503 后成功，max_attempts 默认 3。写出整个 HTTP 响应状态、B 的 report.result.ok 和 report.result.status_code。再用一句话说明为什么 HTTP 状态不能代替逐项检查。
   - 回答：200 403 503 200  False 403 http状态只能表示响应的状态 就算成功200 回来一团乱码也没意义
2. app.py 中，编号检查已经通过，随后 gateway.complete 抛 ValueError("internal test bug")。按今天契约，这个异常是否应变成 DUPLICATE_TASK_ID 的 422？如果把 run_batch 放进捕获编号错误的同一个 try 中，会误报什么？各用一句话回答。
   - 回答：不算吧 放进去的话会报"code": "DUPLICATE_TASK_ID", "message": "duplicate task_id"
3. 自写 test_duplicate_http_request_has_no_calls 输入 A/one、B/two、A/three。若错误实现执行 A/B 后仍返回完全正确的 422 JSON，状态和响应断言能发现吗？写出 factory.calls 的期望值、错误实现实际值，以及能检测差异的那条断言。不要求仅凭失败断言定位错误代码行。
   - 回答：发现不了 [] A和B都有          assert factory.calls == []
        assert factory.gateways["A"].calls == []
        assert factory.gateways["B"].calls == []都可以

## 错题本与验收反馈

### 助手检查（2026-09-23；保留以上原答）

- 业务实现通过：`make_response` 按顺序保留完整嵌套报告与汇总；`analyze_batch` 先把输入转成 Task，只把编号预检查的 ValueError 映射为 422，实际批处理在 except 外运行。空批次与非默认重试上限均符合契约。
- 自写 A/B/A 测试的状态、完整错误体及 factory/gateway/sleeper 零调用断言均有效。原测试 `finally` 把依赖覆盖设为 `lambda: None`，会留下覆盖影响后续测试；助手改为 `app.dependency_overrides.clear()`，保留学习者的测试主体与断言。这是测试隔离修正，不是业务实现故障。
- 本日 73 passed，全仓 410 passed，pip check 与差异空白检查通过。真实本地 HTTP：health 200；样例 200、A/B 顺序和日文原文正常、汇总 2/2/0/2/0；注入 mixed 场景返回 HTTP 200 且 B 报告为上游 403；重复编号和非法上限分别为 422；空批次 200、全零统计。响应无 traceback；临时服务器已停止。既有两项第三方弃用警告不影响通过。
- 复盘第 1 题给出了所需的 HTTP 200、B 的 `ok=False` 和 `status_code=403`，并指出 HTTP 200 不证明内容质量。开头多列的 `403 503 200` 是中间/上游状态，不能当成整个 HTTP 响应的多个状态；本题只有一个整个响应状态 200。
- 第 2 题结论正确：gateway 的 ValueError 不应映射为重复编号；如果把 `run_batch` 放进同一个 try，会误报 `DUPLICATE_TASK_ID`。第 3 题结论正确：状态和 JSON 检不出提前执行；正确 factory.calls 为 `[]`，错误实现实际为 `["A", "B"]`，`assert factory.calls == []` 能检出差异。具体列表值已经在本轮对话说明，此处补准记录，不要求重抄。
- 初始测试记录未填写，不要求回退已完成实现来重现。实际用时与难度由学习者自报，不按开始/结束时间差推算。代码、复盘和学习反馈均已验收，准备按项目规则提交上传。

## 学习反馈

- 实际用时（排除中断，自报）：1h
- 难度与内容量：简单
- 仍需讲解的位置：无自报

- 结束时间：1700
