# Day 16 — 从模型请求到第一次真实调用

状态：2026-09-16 已完成 Gemini A/B/C 三个案例的真实调用、内容核查和复盘；实际用时 2h，结束时间 0800。

按最新混合路线执行：项目开发为主，课程只解释眼前要用的概念。今天的唯一主题是理解我们发给模型的内容，并在配置明确后完成一次真实模型调用。先阅读下面 20～25 分钟的内容，不重做 Day 15，也不增加另一套替身框架。

## 1. 今天只选读这些部分

本地资料：项目根目录 `腾讯FDE教程/` 中名称不带数字后缀的第一份 PDF，完整文件名为《腾讯云 ADP 前沿部署工程师 (FDE) 认证课程 - 腾讯云培训认证.pdf》，共 24 页。以下均为 PDF 页序号，已核对页面文字与配图。

| 位置 | 阅读重点 | 对应项目 |
|---|---|---|
| 第 2 页、3～4 页相关段落，1.1.1 | AI、机器学习、深度学习、生成式 AI 的大致区别；浏览即可，不背历史 | 已有规则解析器与未来真实模型不是同一种实现 |
| 第 7 页下半至第 8 页，1.2.2 | LLM、token、幻觉 | gateway 返回文字不等于返回事实 |
| 第 8 页末至第 9 页前半，1.2.3 | Prompt 中的固定规则与当次任务 | instructions 与 input |
| 第 9 页 1.2.4 开头，到“记忆通常分成两种”前 | 本次请求能看到什么、上下文有上限 | fake.calls 不会自动进入模型上下文 |

来源为本机保存的腾讯课程，原课程链接：[AI 和 Agent 基础](https://cloud.tencent.com/edu/learning/course-4742-84527-84531)。本日已读取本地 PDF，没有核对网页当前版本；互动与视频不包含在本次学习要求中。课程是概念参考，供应商参数需等服务确定后查其官方文档。

阅读不是独立读书报告。下面的解释和现有代码就是今天的落点。

## 2. 先复习一条已有请求（5 分钟）

Day 15 的 INPUT_A 是普通需求原文：

```text
機能: CSV出力
受入条件: 3秒以内
```

在 `Week3/day15/prompt.py` 中，已有正确实现依次做了：

```python
data = {"document": text}                       # Python dict
document_str = json.dumps(data, ensure_ascii=False)  # JSON str
model_request = ModelRequest(
    instructions=EXTRACTION_INSTRUCTIONS,
    input=document_str,
)
```

三种名字别混在一起：text 是原文；data 是包含原文的字典；model_request.input 是这个字典编码后的 JSON 字符串。测试里 `json.loads(model_request.input)` 把它还原成字典，以检查内容是否完整。

类似 Java：先建一个带 document 字段的 Map/DTO，再用 JSON 库序列化成字符串。Python 的 dumps 是编码；loads 是解码。两步都在我们自己的程序里完成，不涉及模型推理。

## 3. 今天真正需要的四个概念

### LLM：根据输入生成文字的模型

已有规则解析器靠我们写的标签规则分类；真实语言模型是在训练中学到语言模式后，对本次输入生成回答。训练已经由供应商完成，我们今天做的是调用，不是重新训练。

课程用“文字接龙”帮助理解常见生成式语言模型：模型根据已有内容逐步生成 token。token 是模型处理的片段，不固定等于一个汉字或一个单词。今天只需要知道它与输入长度、输出长度和费用有关，不做分词器或 Transformer 数学题。

类比边界：它不是 Java 的固定 switch，也不是只拼接几个字的模板函数；输出会受输入、模型和生成设置影响，不能把一次结果当成永远相同的返回值。

### Prompt：告诉模型任务、规则和资料

你昨天写的 EXTRACTION_INSTRUCTIONS 是固定任务规则，例如只返回五个字符串数组，不编造缺项。input 中的 document 是本次要分析的资料。

本项目 ModelRequest 是内部数据对象。供应商可能要求 instructions/input，也可能要求带 role 的消息列表；选定服务后，适配器负责转换，不能仅凭字段同名就认为已经调用了 SDK。

Prompt 改变本次输入，不等于训练或修改模型权重。写“不要编造”有助于表达要求，但不能代替结果检查。

### 上下文：模型本次实际收到的信息

就本项目而言，未来一次请求至少应包括固定规则和当次文档。模型不会因为文件保存在你的电脑里，就自动看见文件内容。

`RecordingGateway.calls` 是我们程序里保存的 Python 列表，用于测试。它没有被自动发给模型，所以记录两次调用不等于给模型建立对话记忆。今天只做独立的单次需求分析，不增加聊天历史功能。

上下文窗口有上限，通常用 token 衡量。当前 `max_text_length` 检查的是 Python 字符串长度，且只检查原文，不包含固定规则；不能用它宣称已经计算模型全部 token。今天不背某个模型的窗口数值。

### 幻觉：回答看起来合理，但缺乏依据或与资料不符

原文只写“希望导出 CSV”，模型却加上“3 秒以内”，就是本项目要检查的无依据补充。

该句完全可以放进合法 JSON 的字符串数组，所以 `decode_requirements` 可能通过。Pydantic 检查字段和类型，不会查证“3 秒”是否出现在需求中。业务缺项检查同样不能证明事实正确。

因此分三层看结果：调用有没有成功、输出结构对不对、提取内容有没有原文依据。

### 课程类比的边界

1.1 的嵌套图是理解今天主流技术的简图。AI 不只包括机器学习；“生成式”描述生成内容的能力，不宜把所有生成方法都强行当成某个固定技术分支。这里不扩展分类史。

“文字接龙”针对本日的生成式文本模型，不等于所有 AI 或所有多模态生成都使用完全相同机制。“看不见当前信息”也不是绝对不能获得信息，而是需要通过实际请求、检索或工具提供；今天没有这些额外功能。

## 4. 现在可以运行：查看即将发送的请求

`preview.py` 已由助手提供，不是新增编码作业。它直接调用你昨天的 build_request，打印实际规则、JSON 输入和解码后的原文，没有调用任何 gateway。

在原项目根目录执行，PowerShell / CMD / Cmder 通用：

```text
.\.venv\Scripts\python.exe -m Week3.day16.preview
.\.venv\Scripts\python.exe -m Week3.day16.preview --case B
```

默认 A 复用昨天的 INPUT_A；B 是没有标签的自然日文需求；C 是缺少验收标准的需求。样例和人工检查要点在 cases.json，全部自制。

观察三处即可：Instructions 是固定规则；Input JSON 是编码后的资料；Decoded document 是解码后恢复的原文。终端中的 Review focus 是我们人工核查时的提示，不会放进发送给模型的请求，也不是模型回答。

正常预览/`--help` 退出码 0；不支持的 case 由 argparse 返回 2；程序只读样例并打印终端，不写文件。PowerShell 用 `$LASTEXITCODE` 查看退出码，CMD 用 `echo %ERRORLEVEL%`。

## 5. 配置确认后继续：真实调用

需要明确：供应商、确切模型名、API 账号是否可用、单次/本日允许的费用边界。只记录这些非秘密信息，密钥通过本地环境配置，不放入聊天或仓库；不因为使用腾讯课程就自动选用腾讯模型。

本次配置已明确为 Google Gemini API 的免费层尝试，模型为 `gemini-3.8-flash`，密钥只通过本机用户级 `GEMINI_API_KEY` 环境变量提供。配置明确后的实现范围限定为：

1. 在本日目录增加所选供应商的 gateway，维持 `complete(ModelRequest) -> str` 的既有约定。`GeminiGateway` 将 `instructions` 映射为 `system_instruction`，将 JSON 字符串 `input` 原样传给官方 Interactions API。
2. 复用 Day 15 的 PromptedModelClient 和 Day 14 的 ModelOutputAnalyzer。只做最小调用和必要错误处理，先不改 HTTP 路由，不增加流式、重试和聊天历史。
3. 在费用边界内先用 A 做一次真实请求；本次随后也完成了 B/C，并保存脱敏结果和观察。
4. 按格式、漏项、编造三项核查，参考 course 4.1 的必要部分（到这一步再选读）。结果填写本日笔记，即使模型答错，也如实保留失败证据。

具体实现见 `gemini_gateway.py` 和 `real_call.py`；离线测试通过后才执行真实调用。当前没有把密钥写入代码或仓库。

### 真实模型运行命令

请先打开一个配置过用户级环境变量的新终端，在项目根目录执行。先只运行 A，避免一次运行多个案例：

```text
.\.venv\Scripts\python.exe -c "import os; print('GEMINI_API_KEY_PRESENT=' + str(bool(os.getenv('GEMINI_API_KEY'))))"
.\.venv\Scripts\python.exe -m Week3.day16.real_call --case A
```

第一条只检查变量是否存在，不会打印密钥。第二条才会调用真实 Gemini API；`--case B` 或 `--case C` 会各自再发送一次请求。正常结果会依次显示模型名、案例、原始模型 JSON、`STRUCTURE_VALID=True` 和解析后的结果；缺少环境变量时退出码为 2。

## 6. 当日成果与状态

- 准备成果：选读与最小讲解、已有请求观察、自制核查样例。
- 已完成：官方 SDK 依赖、Gemini gateway、A/B/C 三个案例真实调用；三次返回结果均通过项目 JSON 结构校验，并完成漏项和编造核查。
- 完成目标：完成所选供应商的最小调用实现、工程检查、至少一个真实请求及内容核查，再填写复盘。
- 如果账号今天无法就绪，可停在准备成果并记录“真实调用待完成”；不把 Day 16 的真实调用目标改写成已完成模拟测试。
- 开始时间、自报用时和结束时间已由学习者填写：0600、2h、0800。无需重写 Day 15 已解释的问答。

今天不需要：AI 历史背诵、注意力公式、模型训练、Embedding/RAG、Memory 实现、Tool/MCP/Agent、多智能体、ADP 界面操作、认证考试和完整 PDF 通读。

## 准备验证

- 2026-09-16：A/B/C 三份请求预览正确，日文和 JSON 解码后的原文一致；帮助退出码 0，无效 case 退出码 2，无 traceback，无输出文件。Day 15 回归 12 passed。
- 2026-09-16：Cmder 日志记录 `real_call --case A/B/C` 三次真实调用，均退出码 0；A 返回 `CSV出力` 与 `3秒以内`，B 保留乱码风险和文字编码待确认，C 没有编造验收条件。三次均通过 `decode_requirements` 结构校验。
