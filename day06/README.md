# Day 6 — Pydantic 数据模型与运行时校验

日期：2026-09-03（日本时间）
计划用时：120 分钟
目标：在 Day 5 CLI 的输出边界加入 Pydantic Schema，让程序不仅有类型标注，还能在运行时检查数据结构。

## 今天为什么学习 Pydantic

下面的类型标注主要帮助 IDE、阅读者和静态检查工具：

```python
requirements: dict[str, list[str]]
```

Python 运行时不会仅因为这条标注就自动拒绝错误数据。Pydantic 会根据模型字段检查真实输入，并在不符合 Schema 时抛出 `ValidationError`。后续 FastAPI 会直接使用同一种模型定义请求和响应。

今天只在程序输出边界使用 Pydantic，不重写 Day 5 的文本解析规则和业务校验逻辑。

## 需要完成的 6 个 TODO

| TODO | 文件 | 内容 |
|---|---|---|
| TODO 1 | `models.py` | 定义 `RequirementData` 的五个 list 字段 |
| TODO 2 | `models.py` | 定义包含版本、需求和错误列表的 `AnalysisOutput` |
| TODO 3 | `cli.py` | 把 parser 的 dict 转换成 Pydantic 输出模型 |
| TODO 4 | `cli.py` | 使用 `model_dump_json()` 写入 JSON |
| TODO 5 | `test_day06.py` | 证明两个模型实例不会共享默认 list |
| TODO 6 | `test_day06.py` | 证明错误字段类型会产生 `ValidationError` |

完成标准：

- Day 5 与 Day 6 合计显示 `25 passed`。
- `RequirementData` 拒绝错误字段类型和未知字段。
- 输出 JSON 包含 `schema_version: "1.0"`。
- 正常输入、文件错误、业务校验失败继续返回 `0 / 1 / 2`。
- 正常输入和业务校验失败仍会生成可读的 UTF-8 JSON。

## 0～10 分钟：复习 Day 5 错题

不看笔记回答：

1. 为什么多异常捕获使用 `(ErrorA, ErrorB)`，不能使用 `ErrorA or ErrorB`？
2. 为什么 package 中的 CLI 推荐使用 `python -m day06.cli`？
3. `WARNING` 和 `ERROR` 在当前业务中的区别是什么？

## 10～20 分钟：安装并确认依赖

从仓库根目录运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements-dev.txt
.\.venv\Scripts\python.exe -c "import pydantic; print(pydantic.__version__)"
```

Day 6 使用 Pydantic 2，因此序列化方法是 `model_dump()` / `model_dump_json()`，不是旧版示例中的 `dict()` / `json()`。

## 20～50 分钟：完成 TODO 1 和 TODO 2

### TODO 1：`RequirementData`

继承 `BaseModel`，并完成以下字段：

| 字段 | 类型 | 默认值 |
|---|---|---|
| `functions` | `list[str]` | 新的空 list |
| `acceptance_criteria` | `list[str]` | 新的空 list |
| `risks` | `list[str]` | 新的空 list |
| `questions` | `list[str]` | 新的空 list |
| `unknown` | `list[str]` | 新的空 list |

每个字段使用 `Field(default_factory=list)`。配置 `ConfigDict(extra="forbid")`，让拼错或多余的字段直接报错。

### TODO 2：`AnalysisOutput`

继承 `BaseModel`，完成：

- `schema_version`：类型为 `Literal["1.0"]`，默认值为 `"1.0"`。
- `requirements`：类型为 `RequirementData`，没有默认值，是必填字段。
- `validation_errors`：`list[str]`，使用 `Field(default_factory=list)`。
- 同样禁止未知字段。

这里有两种“校验”，不要混在一起：

- Pydantic：检查 JSON 的结构和字段类型。
- `validate_result()`：检查业务上是否至少有一条功能和验收条件。

## 50～70 分钟：完成 TODO 5 和 TODO 6

在 `test_day06.py` 中补完两个测试：

- TODO 5：创建两个 `RequirementData()`，只修改第一个实例的 `functions`，证明第二个仍为空。
- TODO 6：把字符串直接传给 `functions`，使用 `pytest.raises(ValidationError)` 证明类型错误被拒绝。

先运行：

```powershell
.\.venv\Scripts\python.exe -m pytest .\day05\test_day05.py .\day06\test_day06.py -q
```

初始脚手架预计为 `18 passed, 7 failed`；完成后应为 `25 passed`。

## 70～95 分钟：完成 TODO 3 和 TODO 4

### TODO 3：`build_output()`

1. 使用 `RequirementData.model_validate(requirements)` 将 parser 的 dict 转成模型。
2. 创建并返回 `AnalysisOutput`。
3. 把业务校验错误传给 `validation_errors`。

### TODO 4：序列化

`run()` 已经拿到 `AnalysisOutput`。使用它的 `model_dump_json(indent=2)` 生成 JSON 字符串，再通过 `Path.write_text(..., encoding="utf-8")` 写文件。

不要再手工组装第二份 payload dict，否则 Schema 修改时容易漏字段。

## 95～110 分钟：自动与手动验收

运行全部 25 项测试：

```powershell
.\.venv\Scripts\python.exe -m pytest .\day05\test_day05.py .\day06\test_day06.py -q
```

手动运行：

```powershell
.\.venv\Scripts\python.exe -m day06.cli .\day06\sample_requirement.txt .\day06\result.json --verbose
```

检查 JSON 顶层结构：

```text
schema_version
requirements
validation_errors
```

## 110～120 分钟：复盘

填写 `day06_notes.md`，尤其说明：

- 类型标注为什么不等于运行时校验。
- Pydantic Schema 与业务校验的职责区别。
- 为什么使用 `default_factory=list`。
- `model_dump()` 和 `model_dump_json()` 的输出区别。

完成后告诉我：

```text
Day 6 完成，请检查
```
