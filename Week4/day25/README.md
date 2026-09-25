# Day25 — 在页面显示前校验 API 报告

状态：2026-09-25 已完成代码、测试、复盘与验收；本日 112 项通过。唯一主题是 HTTP 200 响应的结构与汇总一致性校验，参考 90～120 分钟。Day24 自报 1h、难度中；今天在同一主题内增加一项独立的汇总错误测试。后端仍是本地模拟服务，不能把 `模擬結果` 当作真实模型分析。Day18 的真实对比仍留空，不补交。下方保留原作业步骤，无需回退重现脚手架失败。

本机尚无 Docker CLI 或 Docker Desktop，容器无法实际启动验收。Docker 练习后移；今天可以在现有根 `.venv` 完整学习和验收。

## 0. 按顺序开始

1. 在 [学习记录](./day25_notes.md) 只填开始时间。项目根目录使用 Python 3.11 的 `.venv`。
2. 在项目根运行初始检查，PowerShell 与 CMD/Cmder 都可直接复制：

```text
.\.venv\Scripts\python.exe -m pytest Week4/day25/tests -q --tb=no
```

脚手架预期 **98 passed / 13 failed，退出码 1**。失败集中在今天的模型、`validate_report` 和自写测试占位，不是昨天代码退化。初始检查完成后无需回退重现。
3. 先读第 1～2 节、[ui.py](./code/ui.py) → [ui_client.py](./code/ui_client.py) → [response_models.py](./code/response_models.py)；然后看当天测试，最后做 TODO。
4. 完成后做第 4 节验收，再填写学习记录中的复盘、自报用时和难度。

## 1. 用昨天的例子复习（5 分钟）

Day24 的 [test_day24_extra.py](./tests/test_day24_extra.py) 构造 HTTP 200、B 的 `result.ok=False`、`status_code=403`。`submit_batch` 应返回整份报告，页面把 B 显示为逐任务失败。整个请求若返回 HTTP 500，才走 `HTTPStatusError` → `DemoError("接口请求失败（HTTP 500）")`。今天处理的是第三种情况：HTTP 200，JSON 也能解码，但字段缺失或汇总与明细矛盾。它不能交给 `render_report` 直接索引，否则可能出现页面 traceback 或误导人的数字。

## 2. 最小知识与调用链（20～25 分钟）

```text
Chrome 页面提交
  → ui.py / main
  → ui_client.py / submit_batch：只 POST 一次、检查 HTTP 状态、解码 JSON
  → ui_client.py / validate_report：Pydantic 检查字段与类型，核对汇总
  → 合法 dict → ui.py / render_report
  → 不合法 → DemoError("接口返回结构不符合预期") → 页面错误消息
```

Day24 已有 HTTP 和 JSON 两道关口：`raise_for_status()` 拒绝 422/500，`response.json()` 拒绝不合法 JSON。今天的第三道关口拒绝“合法 JSON、错误内容”。例如 `{"summary":{"requests":2}}` 能被 JSON 解码，却没有页面所需的 `mode`、`tasks` 等字段。类似 Java 的 DTO 入站校验：先得到符合字段要求的对象，再交给显示代码；但 Python 的类型标注本身不做运行时检查，必须实际调用 `BatchResponse.model_validate(body)`。

今天只需会这几项 Pydantic V2 用法：

- `class X(BaseModel)` 中的 `name: str` 是必填字段；`raw: str | None` **没有默认值时仍必填**，只是值允许为 `None`。不要写 `= None`，否则缺字段也可能通过。
- `StrictResponse` 已给出 `ConfigDict(extra="forbid", strict=True)`：嵌套模型继承后拒绝未知字段和把字符串数字自动转成整数。`Field(ge=0)` 表示整数最小为 0；逐任务 `attempts` 最小为 1。
- `BatchResponse.model_validate(body)` 失败抛 `ValidationError`。成功得到模型对象；`model_dump()` 转回页面原本需要的嵌套 dict。`ValidationError` 可能包含收到的数据，不要把异常原文显示在页面。
- Pydantic 检查每个字段的形状和类型；`summary.requests` 是否等于任务行数，需要你另外比较。类型正确不代表统计正确。

与 Day6/14 的请求/模型输出校验是同一思路，只是这里校验**服务返回给页面的报告**。官方补充只查 [Models 的 basic usage 与 model_dump](https://docs.pydantic.dev/latest/concepts/models/) 和 [Fields 的约束字段](https://docs.pydantic.dev/latest/concepts/fields/)；这里的说明与下方练习契约已给出当天所需知识，不用通读整份文档。

最小例子（与作业字段不同）：

```python
from pydantic import BaseModel, ConfigDict, Field

class Ticket(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: str
    priority: int = Field(ge=0)

ticket = Ticket.model_validate({"title": "確認", "priority": 1})
assert ticket.model_dump() == {"title": "確認", "priority": 1}
```

今天不学：`model_validator`、自定义类型、完整 JSON Schema、前端状态管理、异步、真实模型接入、Docker 安装与容器编排、RAG。不要改 Day24 历史文件或后端 API；本日只处理浏览器页面的响应边界。

## 3. 三个 TODO（50～65 分钟）

### TODO 1：response_models.py 的五个响应模型

目的：用字段声明描述 Day24 API 已经返回的报告，给后续校验使用。修改 [response_models.py](./code/response_models.py) 五个 `pass`，保留已给出的 `StrictResponse`。输入是 `BatchResponse.model_validate(body)` 收到的 Python dict；成功输出模型对象，字段错误抛 Pydantic `ValidationError`，不涉及进程退出码、网络或文件。

各层字段全部**必填**，无默认值；列表允许空，所有层拒绝额外字段并启用严格类型：

| 模型 | 字段和类型 | 数值约束 |
|---|---|---|
| `ResultResponse` | `ok: bool`, `raw: str \| None`, `error: str \| None`, `status_code: int \| None` | 无 |
| `RetryResponse` | `result: ResultResponse`, `attempts: int` | `attempts >= 1` |
| `TaskResponse` | `task_id: str`, `report: RetryResponse` | 无 |
| `SummaryResponse` | `requests`, `succeeded`, `failed`, `attempts`, `retries` 都是 `int` | 每个 `>= 0` |
| `BatchResponse` | `mode: Literal["simulated"]`, `tasks: list[TaskResponse]`, `summary: SummaryResponse` | 无 |

提示：`Literal` 从 `typing` 导入，`Field` 从 `pydantic` 导入。`str | None` 允许 null，但该 key 必须存在。模型只检查字段，不在此处重算汇总。合法 A 成功、B 403 失败的完整输入见 [test_response_validation.py](./tests/test_response_validation.py) 的 `valid_body()`。完成时 `BatchResponse.model_validate(valid_body()).model_dump()` 应等于原 dict；缺字段、字符串数字、0 次任务尝试、负数、`mode="live"`、未知字段应抛 `ValidationError`。

### TODO 2：ui_client.py / validate_report

目的：把合法 JSON 变成能安全交给页面显示的报告。修改 [ui_client.py](./code/ui_client.py) 中的占位函数；`submit_batch` 已在 HTTP 200 + JSON 解码成功后调用它，不要重复 POST。

- 输入：任意由 `response.json()` 得到的 Python 值，不假定一定是 dict。
- 第一步：调用 `BatchResponse.model_validate(body)`；若 Pydantic 抛 `ValidationError`，转换为 `DemoError("接口返回结构不符合预期")`，不要把原异常文字拼进页面消息。
- 第二步：用已校验模型的字段核对四组关系：`requests == len(tasks)`；`succeeded` 等于 `result.ok=True` 的行数且 `failed` 等于 `False` 的行数；`attempts` 等于各行 `report.attempts` 的和；`retries == attempts - requests`。任何一项不符，都抛同一条 `DemoError`。
- 全部通过后用 `model_dump()` 返回完整嵌套 dict，不能丢掉失败任务、改变值或修改输入。
- 不捕获 `Exception`；不打印、不写文件、不网络调用。函数无进程退出码，调用它的页面把已知 `DemoError` 显示为消息。

示例：两行任务各一次调用，一行成功一行失败，汇总 `2/1/1/2/0` 合法；若只把 `summary.requests` 改成 3，字段类型仍正确，但必须报 `接口返回结构不符合预期`。HTTP 500 应仍先报告 HTTP 500，JSON 文本非法仍先报告 `接口未返回合法 JSON`。

### TODO 3：tests/test_day25_extra.py 自写边界测试

目的：独立验证**汇总字段错误**不会被页面当成合法报告。修改 [test_day25_extra.py](./tests/test_day25_extra.py) 的占位测试。

1. 复制 `valid_body()` 得到本地 body，再只把 `body["summary"]["requests"]` 改成 `3`；任务列表仍为 A/B 两行，其余字段不变。
2. 在调用前保存 body 的深拷贝，调用 `validate_report(body)`。
3. 用 `pytest.raises(DemoError, match=...)` 断言确切消息 `接口返回结构不符合预期`；再断言输入 body 没被修改。

测试函数无返回值；pytest 全部通过退出 0，有失败退出 1。不要把正式实现写在测试里，也不要删除原有继承测试。最终目标 **112 passed**（其中一项补充测试单独检查只改 `summary.failed` 的情况）。

## 4. 实现后验收（15～20 分钟）

在项目根运行当天测试：

```text
.\.venv\Scripts\python.exe -m pytest Week4/day25/tests -q
```

再启动当天副本的本地模拟 API，PowerShell 或 CMD/Cmder 的终端 1：

```text
.\.venv\Scripts\python.exe -m uvicorn Week4.day25.code.app:app --host 127.0.0.1 --port 8024
```

终端 2 启动页面：

```text
.\.venv\Scripts\python.exe -m streamlit run Week4/day25/code/ui.py --server.address 127.0.0.1 --server.port 8525 --server.headless true --browser.gatherUsageStats false
```

`ui.py` 继续向固定本地端口 8024 发请求；若 Day24 的 API 仍占用该端口，先在其终端 Ctrl+C 停止，再启动 Day25 API。不要同时启动两个同端口 API。在 Chrome 打开 [Day25 页面](http://127.0.0.1:8525)：A 默认值提交，应看到一个成功任务及 `1/1/0/1/0`；B 填 `文字コードを確認する。` 再提交，应看到 A/B 两行及 `2/2/0/2/0`。页面原有空 A、超长 A、连接错误行为应保留。错误结构和汇总矛盾用无网络测试替身覆盖；默认模拟 API 不会自然产生这些错误，勿把注入值描述为真实服务结果。完成后用 Ctrl+C 关闭由本日启动的两个服务。

填写 [学习记录](./day25_notes.md) 的复盘、自报实际学习时长及难度后交给助手验收。建立脚手架和助手验证不代表学习者已完成。

## 5. 助手建立记录

- 从 Day24 复制当天所需 code、tests 和脱敏样例，统一改为 `Week4.day25` 路径；Day24 历史文件未改。复制后 Day25 原有 **91 passed**，证明复制行为保留。
- 新增响应模型和 `validate_report` 占位、结构/汇总测试及自写测试占位；当前 **98 passed / 13 failed** 是预期 TODO 状态。原 Day24 的空批次测试样例在当天副本中补全五个 summary 字段，以匹配真实 API 返回结构。
- 根 `.venv` Python 3.11、`pip check` 通过。未增加依赖；Pydantic 已在 requirements-dev.txt。未安装 Docker、未声称容器验收。浏览器手动验收留待实现后进行。

### 最终验收（2026-09-25）

五个响应模型、`validate_report` 和自写汇总矛盾测试均已实现。助手针对只修改 `summary.failed` 的漏检补了原契约测试；最终 Day25 112 passed、pip check 通过。Chrome 实测 A、A+B、空白/超长输入、API 停止后的连接提示与重启后恢复均通过；详细结果、复盘补准和学习者自报用时见当天笔记。
