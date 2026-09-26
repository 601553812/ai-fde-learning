# Day26 学习记录 — 显式选择本地模拟或真实模型

## 学习开始

- 开始时间：1732
- 环境确认：

## 学习目标（无需提前作答）

- 沿当前代码说明表单到网关的调用链，以及模拟与真实模式在哪一步分开。
- 说明没有密钥时为何在创建网关前返回 503。
- 区分真实调用成功与提取内容正确。

## 执行记录（学习后填写）

- 初始脚手架测试结果：
- 完成后当天测试结果：
- Chrome 默认模拟模式结果：
- Chrome 真实模式一次短句结果或无法验证的具体原因：
- 主要错误及修正：

## 学习后复盘（完成实现后用自己的话回答）

1. 在 `code/runtime.py`，请求 `POST /analyze-batch?mode=live` 带一条 A 任务，但服务进程里两个 API key 环境变量都不存在。HTTP 状态和 `detail` 应是什么？`GeminiGateway` 会创建几次？按“HTTP / detail / 创建次数”回答。
   - 回答：503 detail={"code": "MODEL_NOT_CONFIGURED", "message": "Gemini API key is not configured"} 0
2. 在 `code/app.py`，A 的文本为 `一覧をCSVで出力する。`，批次只有 A 一项，`max_attempts=1`。使用 `mode=simulated` 时，返回的 `mode`、`raw`、`summary.requests`、`summary.attempts` 分别是什么？只把模式改成 `live` 后，结合已知的一项任务和一次调用上限，这四项中哪些已经能确定，哪一项要等模型调用结果？按“模拟四项 / live 已知项与待定项”回答。
   - 回答：mode simulated raw "模擬結果：A"  summary.requests 1 summary.attempts 1 改成live mode能确定 其他都要等结果
3. 在 `code/ui_client.py`，一次 live 请求返回 HTTP 200、字段和汇总合法、A 的 `result.ok=True`，但 `raw` 漏掉了输入中明确的 CSV 要求。今天的 `validate_report` 会拒绝吗？这能否证明需求提取正确？按“校验结果 / 内容结论”回答。
   - 回答：不会拒绝 不能

## 错题本与验收反馈

- 助手任务单更正：最初要求先 `setenv` 一个假密钥、再删除、最后断言响应不含该假值；删除后这个断言不能有效验证泄露边界，属于助手测试设计问题。TODO 2 已改为直接清除两个密钥并断言固定 503 与零网关创建，不计为学习者错误。
- 助手验收（2026-09-26；保留上方原答）：原 117 项测试通过，`pip check` 与差异检查通过。TODO 1 写明两个密钥都没有**值**才报 503；当前 `is None` 会把两个空字符串误认成已配置，新增原契约边界测试后为 **117 passed / 1 failed**。需在 `code/runtime.py` 按“值是否非空”判断，再跑当天测试，完成目标 118 passed。自写缺密钥测试已断言 503、固定 detail 与 `created == []`。
- Chrome 人工核对：默认模拟提交 A 显示 `mode=simulated`、`模擬結果：A`、任务/成功/失败/调用/重试为 `1/1/0/1/0`。用户此前报告一次 live 页面 `呼び出し失敗: timeout / 上流ステータス: None`；助手未重发付费请求，真实模型成功返回尚无证据。初始测试记录与 Chrome 结果等学习者执行栏仍空，不能代填为学习者操作。
- 复盘第 1、3 题正确。第 2 题模拟模式的 `raw` 实际为 `模擬結果：A`，不是原答中的 JSON；题目原先把“仅凭模式”和“结合已给定输入”混写，现已把一项任务、一次上限及所问范围写清。live 模式下 `mode=live`、`requests=1`、`attempts=1` 已可确定；`raw` 取决于调用结果，超时等失败时为 `None`。这段澄清为助手反馈，不记为学习者独立作答，也不要求重抄已经答对的部分。Day26 暂不标记完成或提交上传。
- 用户明确要求本次只以代码、测试和 Cmder 日志检查，不需要 Chrome 验收。此前助手的 Chrome 观察保留为历史记录，不作为本次完成门槛。
- Cmder 过程（仅 2026-09-26、Day26 相关日志）：可确认五次完整的当天 pytest 尝试，依次为 `115 passed / 2 failed`（初始 TODO）、一次收集阶段 `ModuleNotFoundError: code.api_models`（退出 2、未执行测试）、`115 passed / 2 failed`、`116 passed / 1 failed`、`117 passed`。中间同一密钥判断失败出现两轮，随后通过；日志能证明命令与报错，不能证明编辑过程或学习者想法。另有本地 API 访问记录：模拟模式两次 HTTP 200、live 两次 HTTP 200；访问日志没有逐任务结果，因此不能据 HTTP 200 判断 live 调用成功。两项服务启动命令后没有对应下一条 `CMD_META` 完成标记，不据此推断服务已退出。日志未检出常见密钥字面模式；不复制日志原文到公开仓库。
- 学习者自报用时原值 `2h-` 保留，不按 Cmder 的开始/结束时间或命令间隔推算。
- 本次最终复查：当天 **117 passed / 1 failed**，全仓 **730 passed / 同 1 failed**，失败均是空字符串密钥边界；`pip check`、已跟踪文件 `git diff --check` 通过。全仓运行是助手检查复制包相关回归，未要求学习者重跑历史学习日。
- 再次复查（2026-09-26）：`code/runtime.py` 的 `is None` 判断未变；本日仍 **117 passed / 1 failed**，失败同为空字符串密钥边界。Cmder 日志自上次检查后没有新增完整的 Day26 pytest 运行记录。学习者已将第 2 题模拟 `raw` 订正为 `模擬結果：A`；live 一项任务、`max_attempts=1` 时，`summary.requests=1` 和 `summary.attempts=1` 可在调用前由输入和上限确定，当前回答“其他都要等结果”仍需澄清。此前反馈保留为历史，不计重复错误。
- 最终收尾（2026-09-26）：学习者修正后当天 **118 passed**，助手全仓 **731 passed**；`pip check` 和差异检查通过。缺失/空字符串密钥返回固定 503，有一个有效密钥时选择真实网关工厂且延迟创建；自写测试证明缺失密钥时 503、固定 detail、零网关创建。复盘第 1、3 题正确；第 2 题学习者已订正模拟原文，live 的 `mode=live`、`requests=1`、`attempts=1` 与 `raw` 待结果的区别由助手补准，不记为独立作答，也不要求重抄。本日代码与复盘收尾完成；真实模型输出仍未验证成功，先前逐任务 timeout 仅证明错误路径。
- Cmder 后续过程：在先前五次完整 pytest 之后，还可确认七次完整尝试，依次为两次 `StringUtil` 导入导致收集失败（退出 2）、`116 passed / 2 failed`、两次 `117 passed / 1 failed`（缺密钥分支对 `None` 调用 `.strip()`）、`117 passed / 1 failed`（单个密钥误报 503）、最终 `118 passed`。这些记录只证明终端命令与结果；不能据此推断编辑时刻、思路或学习时长。用户自报 `2h-` 仍是实际用时记录。

### 错题本：本日反复出现、现已修正

- 导入不存在的模块：错误版本 `import StringUtil`；正确做法是使用 Python 字符串已有的 `.strip()`，例如 `"  x  ".strip() == "x"`。`StringUtil` 不是本项目安装或提供的模块，所以 pytest 在收集测试、导入 `runtime.py` 时就报 `ModuleNotFoundError`，业务测试尚未执行。日志中相同导入错误出现两轮。
- 对缺失环境变量直接调用字符串方法：错误版本 `os.getenv("GOOGLE_API_KEY").strip()`；正确版本先保存值并判断是否存在，再检查非空内容，例如 `key = os.getenv("GOOGLE_API_KEY"); has_value = bool(key and key.strip())`。变量不存在时 `os.getenv()` 返回 `None`，而 `None.strip()` 会抛 `AttributeError`；日志中这一错误在三轮相关测试输出中持续出现，最终实现已加存在性检查。

## 学习反馈

- 实际用时（排除中断，自报）：2h-
- 难度与内容量：中
- 仍需讲解的位置：无

- 结束时间：2039
