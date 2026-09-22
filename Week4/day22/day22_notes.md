# Day22 学习记录 — 顺序批处理

## 学习开始

- 开始时间：1312
- 环境确认：原项目根目录，根 .venv Python 3.11；按 README 第 0 节先运行初始测试。

## 学习目标（无需提前作答）

- 用任务编号把原文与最终调用报告对应起来。
- 区分获取 gateway、实际调用次数与最终任务数。
- 先检查整批，再执行；已知任务失败后继续后续任务。

## 执行记录（做完填写）

- 初始测试：
- 实现后本日 / 全仓测试：助手最终复查本日 56 项、全仓 337 项通过。
- mixed 默认与上限 1 的统计 / 退出码：助手验收分别 3/2/1/4/1、退出 1；3/1/2/3/0、退出 1。
- duplicate 与 empty 的输出 / 退出码：助手验收分别 duplicate task_id、退出 2；空明细与全零统计、退出 0。

## 学习后复盘

1. 本日 run_batch_demo 的 mixed 默认上限 3：A 直接成功，B 返回 403，C 先 503 后成功。分别写 factory.calls 的顺序、C gateway.calls 的长度、最终任务总数。这题检查获取对象与实际调用的区别，不要求重答昨日五项统计。
   - 回答：A B C 2 3
2. 本日自写 test_duplicate_id_rejects_whole_batch_before_calls 输入编号 A/B/A。若错误实现执行 A、B 后才抛相同 ValueError，pytest.raises 会通过吗？factory.calls 的期望与实际分别是什么？哪条断言能检测这个差异？这题检查为什么仅有异常断言不够。
   - 回答：会通过 期望就是测试里写的 实际是factory.calls == ["A","B"]    assert factory.calls == []能检测 其他部分也能抛出ValueError吧
3. test_nondefault_attempt_limit_applies_to_every_task 中 A、B 都先返回 503，传入 max_attempts=1。各任务应调用几次、sleeper.calls 应是什么？如果 run_batch 漏传 max_attempts，已有默认值 3 会让本例实际发生什么？这题检查配置是否传到了真正执行重试的位置。
   - 回答：各任务调用1次 sleeper.calls应该是空 会让AB都各自重试

## 错题本与验收反馈

### 助手检查（2026-09-22；保留以上原答）

- 业务实现正确：整批校验在循环前，按任务取 gateway，保留原文与顺序，传递 max_attempts/sleeper，已知失败继续，未知异常传播。当前全仓 337 passed（包含 Day22 全部 56 项），pip check、diff --check 通过；两条既有依赖弃用警告不影响通过。
- 独立进程核查帮助/非法参数/mixed/mixed 上限 1/duplicate/empty，退出码 0/2/1/1/2/0；完整 JSON、任务顺序、中文日文 UTF-8、无 traceback、临时目录无输出文件通过。另直接观察重复编号场景，factory、两个 gateway 和 sleeper 记录均为空。未读取 Cmder 日志，不推断学习者尝试次数。
- 自写测试当前能通过，也能通过前置的 factory.calls 断言检测提前执行；但后续 factory("A") 和 factory("B") 会调用 __call__，给 factory.calls 新增记录。建议改为直接读取 factory.gateways["A"].calls 与 factory.gateways["B"].calls，观察时不改变记录。尚未代改学习者代码，不把它说成业务实现失败或整个测试无效。
- 复盘第 1 题正确：factory.calls 为 ["A", "B", "C"]，C 实际调用 2 次，总任务数 3。
- 复盘第 2 题需订正：题设明确错误实现执行 A、B 后才抛出相同 ValueError，因此 pytest.raises 会通过；factory.calls 的期望是 []，实际是 ["A", "B"]，不是 ["A", "B", "A"]。assert factory.calls == [] 会失败。pytest.raises 检查异常类型和消息，不证明异常来自哪个函数；同一代码块内其他位置抛出匹配异常也可能通过。此处检测到差异，不等于直接定位根因。
- 复盘第 3 题正确：上限 1 时各调用一次，sleeper.calls=[]；若漏传而使用默认 3，本测试的第二项都是 "unused" 字符串，故各调用两次后成功，总共等待两次，记录 [0.2, 0.2]，并非一定用满三次。
- 可选命名建议：validate_task_ids 中的 set 实际是 list，也遮蔽 Python 内置 set 名称，改名 seen_ids 更清楚；当前不影响行为，不新增验收要求。
- 实际用时自报 1h，难度简单；开始 1312、结束 1443 保留。不按时间差推算用时。当前业务验收通过，待测试观察写法与第 2 题澄清后收尾，尚未提交推送。

### 最终收尾（2026-09-22）

- 学习者已把两处观察改为 factory.gateways[编号].calls，不再通过调用 factory 改变记录。第 2 题已改为 raises 会通过、错误实现记录为 ["A", "B"]，结论正确；第 1、3 题也正确。本日代码、测试与复盘验收完成，上方待订正/未收尾为历史状态。
- 第 2 题此前原答为“不会”，并认为实际记录是 ["A", "B", "A"]；此处保留原答历史。经对话逐步解释后由学习者订正，不记为首次无提示独立掌握，不再追问或要求重抄。
- 本次概念讲解：RecordingFactory({...}) 创建实例并运行 __init__；factory("A") 调用实例并运行 __call__，此时才记录编号。传递 factory 参数、读取 factory.gateways 不触发 __call__。类名大写/实例名小写只是惯例，应以定义和赋值判断。Java 可类比 Function.apply，但 Python 不需实现该接口。
- 最终复测全仓 337 passed（本日 56 项），pip check 通过；本轮仅修改测试观察写法与复盘，业务代码未变，沿用前轮独立 CLI 验收证据。公开提交不含本地 Day18 的 11 项，提交范围对应 326 项。
- 实际用时仍为自报 1h，难度简单；开始 1312、结束 1443 保留。下次先用当天两行真实代码简短复习创建对象与调用对象，再按路线推进，适量增加独立功能，不补交 Day18。按默认规则提交并同步 GitHub，结果以 Git 核对为准。

## 学习反馈

- 实际用时（排除中断，自报）：1h
- 难度与内容量：简单
- 仍需讲解的位置：无

- 结束时间：1443
