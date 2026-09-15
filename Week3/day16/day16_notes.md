# Day 16 学习记录

## 学习开始

- 开始时间：0600
- 环境确认：原项目根 .venv / Python 3.11；Gemini 官方 Python SDK 已安装，密钥只配置在本机用户级 `GEMINI_API_KEY` 环境变量。

## 本日目标（无需提前作答）

- 把 LLM、Prompt、上下文、幻觉对应到已有代码。
- 配置明确后执行第一次真实模型调用，分别核查调用、结构和内容。

## 账号与调用边界（只填写非秘密信息）

- 供应商：Google Gemini API。
- 模型名：`gemini-3.8-flash`。
- API 账号状态：已配置并成功完成 A/B/C 三次真实调用。
- 免费额度或费用上限：使用免费层尝试；本次实际费用未记录，以控制台为准。
- 当前状态：A/B/C 均已调用；复盘已填写；实际用时和结束时间待学习者补充。

## 实际调用与核查（执行后填写）

| Case | 是否实际调用 | 调用结果 | 结构校验 | 是否漏项/编造及原文证据 |
|---|---|---|---|---|
| A | 已调用 | 成功；返回合法 JSON | 通过 `decode_requirements` | `functions` 为 CSV 出力，`acceptance_criteria` 为 3 秒以内；与原文一致，未发现编造 |
| B | 已调用 | 成功；返回合法 JSON | 通过 `decode_requirements` | `functions` 为订单列表 CSV 导出，`acceptance_criteria` 为 3 秒以内，`risks` 记录乱码担忧，`questions` 保留确认文字编码；未擅自决定 UTF-8 或 Shift_JIS |
| C | 已调用 | 成功；返回合法 JSON | 通过 `decode_requirements` | `functions` 为订单列表 CSV 导出，`acceptance_criteria` 为空；没有编造 3 秒以内等验收条件 |

只粘贴自制样例的脱敏模型输出，不保存请求头、密钥或完整 SDK 异常。API 提供的 token 使用量与费用如有记录，应注明来源；不知道就写未记录，不凭字符数推算。

### A 的脱敏原始输出

```json
{"functions":["CSV出力"],"acceptance_criteria":["3秒以内"],"risks":[],"questions":[],"unknown":[]}
```

### B/C 的脱敏原始输出

```json
{"functions":["注文一覧をCSVで出力したい"],"acceptance_criteria":["出力は3秒以内に完了すること"],"risks":["文字化けが心配"],"questions":["文字コードは担当者に確認したい"],"unknown":[]}
```

```json
{"functions":["注文一覧をCSVで出力する"],"acceptance_criteria":[],"risks":[],"questions":[],"unknown":[]}
```

### Cmder 日志核对

- 07:17 左右：环境变量存在性检查输出 `True`，没有输出密钥。
- 约 07:41：A 真实调用完成，退出码 0。
- 约 07:41～07:50：B 真实调用完成，退出码 0。
- 约 07:50：C 真实调用完成，退出码 0。
- 三次输出都显示 `MODEL=gemini-3.8-flash`、`STRUCTURE_VALID=True` 和解析结果；日志中未出现 traceback 或输出文件操作。
- 时间范围只用于还原命令顺序和结束上界，不据此推算实际学习用时。

## 学习后复盘

1. 假设处理 cases.json 的 C，模型生成了“3 秒以内”且 JSON 字段类型都合法。decode_requirements 是否一定拒绝？为什么还需要对照原文？用两句说明。

答：不会拒绝 我们现在没做字段类型以外的校验吧 就是单纯检验一下是否和我们想定的输出一致

2. 第一次调用 A 后，Python 的 fake.calls 记录了它；第二次只发送 B 的规则和文档。模型会因为该列表存在就收到 A 吗？指出信息是否被发送即可。

答：咱们今天用的PromptedModelClient,传入的参数是GeminiGateway 而fake.calls的存储追加逻辑在RecordingGateway里 所以应该不会收到A

验收者补充：两题结论正确。`decode_requirements` 会检查 JSON、字段集合和字符串数组类型，但不能判断“3 秒以内”是否真的出现在 C 的原文中；`fake.calls` 只是 `RecordingGateway` 的本地记录，不会自动进入发送给 Gemini 的 B 请求。

## 验收与学习反馈

- 请求预览：助手已验证 A/B/C、日文 JSON 原文还原、帮助/错误参数退出码 0/2、无 traceback 和输出文件；Day 15 回归 12 passed。预览不能作为真实调用证据。
- 最小 gateway 实现与工程检查：`GeminiGateway` 离线映射测试通过；真实入口为 `Week3.day16.real_call`。
- 真实调用与结果核查：A/B/C 均完成；三次结构校验通过，内容核查见上表。
- 难度与内容量：
- 仍需讲解的位置：
- 实际用时（排除中断，自行填写）：2h

- 结束时间：0800
