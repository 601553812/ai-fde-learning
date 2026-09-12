# Day 13 — 环境变量与安全配置

日期：2026-09-12（日本时间）

状态：已完成学习与验收（本日 14 passed，全仓 123 passed）；旧导入已清理，复盘已收尾。文档整理已获确认，随本次学习成果提交。下方 TODO 保留为原作业说明。实际用时：学习者自报 1.5h。

## 今天为什么学这个

之前“最多 2000 字符”写在代码里。现在希望同一份代码，在一个环境里限制 80 字符，在另一个环境里限制 2000 字符，不必修改源码。以后外部服务地址、超时也有类似配置需求，今天只处理一个不敏感的整数配置，不使用任何真实密钥或外部 AI 服务。

唯一主主题是“从环境读取、校验并使用配置”。按 Day 12 反馈增加独立实现量：除了读取有效值，还要拒绝无效配置、验证非默认边界和错误后的恢复。不重复已口头确认的 Depends 问题，不因为中间日期没有新学习记录而补课。

## 最小知识：先读这一节，再看 TODO

### 1. 环境变量不是 HTTP 请求参数

环境变量可以先理解为启动程序时交给它的一组“名称 → 字符串值”。本题名称固定为 AI_FDE_MAX_TEXT_LENGTH。它由运行服务器的人设置，不由调用 API 的客户端通过 JSON 或 query 设置。

Java 对照：`System.getenv("NAME")` 与 Python 的 `os.getenv("NAME")` 用途相近；Python 的 getenv 还能传缺失时的默认值。这里不是 Spring 配置注入，也不是 Java 的 `System.getProperty`。

```python
import os

raw = os.getenv("EXAMPLE_LIMIT", "30")
# 没设置时得到字符串 "30"，不是整数 30。
number = int(raw)
# int("hello") 会抛 ValueError，需要按业务要求处理。
```

官方依据：[Python 3.11 os.getenv](https://docs.python.org/3.11/library/os.html#os.getenv)。只需要读取、默认值和字符串类型，不用阅读整个 os 模块。

### 2. 读取、转换、校验是三步

本题最终需要的是 Settings(max_text_length=80)，字段值必须为 int。Settings 使用以前学过的 dataclass，定义已提供；dataclass 和类型标注不会自动把字符串转成整数或检查取值范围，这些由 load_settings 实现。

规则只有这几条：

- 环境变量不存在：默认 2000。
- 存在：按 Python 的 int(raw) 转换，整数必须在 **1～10000，含两端**。
- "80"、"1"、"10000"、" 120 " 有效；int 支持的整数文本形式可接受，无需自己写正则。
- 空字符串、"not-a-number"、"2.5"、"0"、"-1"、"10001" 无效。
- 无效值必须抛 ConfigurationError(CONFIG_ERROR_MESSAGE)，不悄悄退回 2000，不把原始值拼进错误信息，不打印整个环境。

不要用“空值就取默认值”混淆未设置和设置为空；默认只适用于不存在。int 转换失败时捕获 ValueError；不要捕获所有 Exception 隐藏编程错误。

### 3. 接到已经理解的 Depends

先读 settings.py，再读 app.py。今天同时传入两个不同职责的对象：

```python
settings: Settings = Depends(get_settings)
analyzer: RuleBasedAnalyzer = Depends(get_analyzer)
```

第一个提供“配置数据”，第二个提供“做分析的对象”，都是原来的 Depends 用法，不是新的注入机制。get_settings 调用 load_settings；对已知 ConfigurationError 转换为固定 503 的适配代码已提供，不需要重写。

路由函数体已提供：先用 settings.max_text_length 检查长度，再调用已有分析器，最后执行 strict 业务策略并返回结果。长度检查用配置值；原有解析器、AnalysisOutput、strict 和服务不可用处理继续复用，不修改历史日文件。

### 4. 无效配置与超长请求，不是同一种错误

- 配置合法，但客户端文本超过上限：413，detail 使用 TEXT_TOO_LONG、实际配置上限和实际字符数。
- 服务端配置无效：503，detail 固定为 `{"code": "CONFIGURATION_INVALID", "message": "Server configuration is invalid"}`。客户端修改文本不能修好服务器配置。
- 分析器暂时不可用：仍沿用已有 503/ANALYZER_UNAVAILABLE，不能与配置错误混用 code。

这里的 503 是本练习约定；生产系统也可能在启动时直接拒绝无效配置。今天不扩展启动生命周期。/health 只表示进程能响应，不读分析配置，因此配置错误时它仍可返回 200，不代表分析接口可用。

### 5. 用测试临时设置环境，不修改电脑的永久配置

```python
monkeypatch.setenv("EXAMPLE_LIMIT", "40")
monkeypatch.delenv("EXAMPLE_LIMIT", raising=False)
```

第一行在测试进程内临时设置字符串值；第二行临时移除变量，raising=False 表示原本不存在也不报错。和前面的 setitem 一样，测试结束后恢复原状态，with context 也能限定更小范围。依据：[pytest 环境变量替换](https://docs.pytest.org/en/stable/how-to/monkeypatch.html#monkeypatching-environment-variables)。

本题每次调用 load_settings 都读取当前 Python 进程的环境，不在模块顶层缓存。测试修改 os.environ 所表示的进程环境后，下一次请求应读取新值。但在另一个终端修改变量，不会自动改变已运行服务器的环境；手动实验要在设置变量的终端重新启动服务器。

## 四个 TODO

### TODO 1：读取并校验配置

修改 settings.py 的 load_settings。

- 输入：当前进程环境里的 AI_FDE_MAX_TEXT_LENGTH，无显式函数参数。
- 按上面的三步规则读取、转换、检查范围，返回 Settings(max_text_length=校验后的整数)。替换只返回默认值的脚手架。
- 异常：无效整数文本或范围不合法时，抛 ConfigurationError(CONFIG_ERROR_MESSAGE)；可用 raise ... from error 保留转换原因，不暴露原值。
- 完成条件：默认值、非默认值、两端边界、空字符串、非整数和范围错误测试通过；同进程修改配置后重新读取能够生效。

### TODO 2：长度检查真正使用传入上限

修改 app.py 的 check_text_length(text, max_text_length)。

- 输入：原始 str text，以及已经校验好的整数上限。
- len(text) 小于等于上限时正常返回 None，不改变 text。
- 超出时抛 HTTPException，status_code=413，detail 为 `{"code": "TEXT_TOO_LONG", "max_length": max_text_length, "actual_length": len(text)}`。
- 替换旧固定 2000 的委托，删除不再使用的 old_check_text_length 导入。不重复解析需求、不重写路由或分析器。
- 完成条件：非默认配置边界生效；响应中的 max_length 也反映实际配置，不能只改判断条件而保留写死的错误字段。

### TODO 3：配置上限拦截后不调用分析器

修改 test_day13.py 的 test_custom_limit_rejects_before_analyzer_call，替换 pytest.fail。

1. 用 monkeypatch.setenv 把 ENV_NAME 设置成字符串 "12"。
2. 创建并保存 FixedAnalyzer(make_fixed_output())，用具名函数返回它，再覆盖 get_analyzer。
3. POST，body 为 `{"text": "あ" * 13}`。
4. 检查 413，完整 JSON 为 `{"detail": {"code": "TEXT_TOO_LONG", "max_length": 12, "actual_length": 13}}`，并断言 fake.calls 为 []。

只证明 analyze 没执行，不要求提供分析器的函数也没执行。

### TODO 4：修好配置后下一次请求恢复

修改 test_repaired_configuration_allows_the_next_request，替换 pytest.fail。

1. 准备 expected = make_fixed_output()、同一个 fake = FixedAnalyzer(expected)，用具名函数覆盖 get_analyzer。
2. 环境设为 "bad"，POST VALID_TEXT，确认 503、完整 body 为 CONFIG_ERROR_BODY、fake.calls 为 []。
3. 在同一个测试里把环境改为 "80"，再次 POST 同一个 VALID_TEXT；确认 200、完整 JSON 等于 expected.model_dump()、fake.calls 精确为 [VALID_TEXT]。

验证目的：无效配置不能继续分析，也不能悄悄退回默认值；配置读取不能只在 import 时进行。不要手动清空 calls 或重新创建 fake 来掩盖第一次请求的行为。

## 学习顺序与自动检查

建议：最小知识和非测试代码约 25 分钟；TODO 1/2 约 30～40 分钟；TODO 3/4 约 20～30 分钟；手动验证与四题复盘约 15～25 分钟。按实际消化调整，不堆高级概念。

根目录执行，PowerShell / CMD / Cmder 通用，无需安装新依赖：

```text
.\.venv\Scripts\python.exe -m pytest day13/test_day13.py -q --tb=short
```

准备验收时再运行回归：

```text
.\.venv\Scripts\python.exe -m pytest day11/test_day11.py day12/test_day12.py day13/test_day13.py -q --tb=short
```

初始预期本日 6 passed / 8 failed：默认旧行为仍能运行，环境配置相关行为和两项学生测试尚未完成。失败应只来自本日 TODO，不是安装故障。全部完成目标：本日 14 passed，Day 11～13 为 35 passed，全仓 123 passed。脚手架实测结果另行补充，不将目标数量当成已经通过。

脚手架实测（2026-09-12）：本日 6 passed / 8 failed，全仓 115 passed / 8 failed，历史 109 项保持通过；pip check 通过。分别用未设置、80、bad 三种环境启动临时 HTTP 服务，health、docs、OpenAPI 参数位置、日文 UTF-8、默认 2000 字符拒绝和无输出文件检查通过。当前 80/bad 均被脚手架忽略，81 字符仍返回 200，明确属于 TODO，不能当作配置功能完成。三个验收进程均已停止，没有修改永久环境；UTF-8、JSON 样例、敏感信息和差异空白检查通过。作业仅保存在本地，尚未提交上传。

## 手动验证（完成 TODO 后再做）

新开一个实验终端，只设置这个临时变量，不用 setx 或修改系统永久环境。

PowerShell：

```powershell
$env:AI_FDE_MAX_TEXT_LENGTH = '80'
.\.venv\Scripts\python.exe -m uvicorn day13.app:app --host 127.0.0.1 --port 8013
```

CMD / Cmder：

```bat
set "AI_FDE_MAX_TEXT_LENGTH=80"
.\.venv\Scripts\python.exe -m uvicorn day13.app:app --host 127.0.0.1 --port 8013
```

另一个终端发送请求，两种 shell 通用：

```text
curl.exe -i http://127.0.0.1:8013/health
curl.exe -i -H "Content-Type: application/json" --data-binary "@day13/sample_request.json" http://127.0.0.1:8013/analyze-requirement
.\.venv\Scripts\python.exe -c "import requests; s=requests.Session(); s.trust_env=False; r=s.post('http://127.0.0.1:8013/analyze-requirement', json={'text':'x'*81}, timeout=5); print(r.status_code); print(r.json())"
```

完成后预期依次为 200/ok、200/日文结果、413/max_length=80/actual_length=81。当前脚手架忽略配置，最后一项可能仍为 200，这是待完成行为。

Ctrl+C 停止服务，在同一个启动终端把变量值改成 bad 并重新启动；样例请求应返回固定 503/CONFIGURATION_INVALID，不含原始配置值，/health 仍为 200。初始脚手架对此也暂不拒绝。打开 http://127.0.0.1:8013/docs 可查看接口，客户端输入仍只有 text body 和 strict query，不要求传 settings/analyzer。

结束后 Ctrl+C 停止服务。PowerShell 用 `Remove-Item Env:AI_FDE_MAX_TEXT_LENGTH -ErrorAction SilentlyContinue` 清理；CMD 用 `set "AI_FDE_MAX_TEXT_LENGTH="` 清理。关闭该实验终端也会丢弃它的临时配置，不改变其他已运行进程。清理后重新启动验证默认上限恢复为 2000。curl 的进程退出码不等于 HTTP 状态码，应看响应中的状态。

## 完成标准和今天不学的内容

除了测试数量，还要验收非默认配置确实影响路由、错误响应准确且不泄露配置、错误后的恢复、旧 strict/Schema/分析失败行为、日文 UTF-8 和不生成输出文件。不要修改旧测试、skip/xfail 或写死测试结果来过关。

只填写四题复盘和实际用时，结束时间放最后一行。说“Day 13 完成，请检查”后最终验收，按规则更新进度并同步 GitHub；当前只建立作业，不是完成学习。

今天不学 .env 文件加载、pydantic-settings、新 SDK、真实密钥、缓存/单例、启动生命周期、动态配置中心、异步、数据库、Docker 或外部 LLM 调用。环境变量也不是秘密保险箱，不应把敏感值打印或提交仓库。
