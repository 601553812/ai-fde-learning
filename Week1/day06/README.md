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

## 开始前：今天只学这 7 个知识点

不需要先阅读整份官方文档。Day 6 只使用下面这些内容，其他 Pydantic API 暂时不学。

### 1. `BaseModel` 是什么

`BaseModel` 可以先理解为：

```text
Java DTO + 构造数据时的类型检查 + JSON 序列化
```

定义模型时继承它：

```python
from pydantic import BaseModel


class User(BaseModel):
    name: str
    age: int
```

`name` 和 `age` 是模型允许的数据字段。

### 2. 必填字段和默认字段

没有默认值的字段必须提供，有默认值的字段可以省略：

```python
name: str
schema_version: str = "1.0"
```

### 3. list 默认值使用 `default_factory`

```python
from pydantic import Field

tags: list[str] = Field(default_factory=list)
```

它可以先类比为 Java 每次创建 DTO 时都执行 `this.tags = new ArrayList<>()`，因此每个模型实例都有自己的 list。

### 4. `model_validate()`：把外部数据变成模型

```python
user = User.model_validate({"name": "田中", "age": 30})
```

成功后得到 `User` 对象，可以使用 `user.name`。数据无法满足字段类型时会抛出 `ValidationError`。

### 5. `ConfigDict(extra="forbid")`：拒绝未知字段

```python
class User(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
```

如果输入错写成 `user_name`，程序会明确报错，而不是悄悄忽略它。

### 6. `Literal`：字段只能是固定值

```python
schema_version: Literal["1.0"] = "1.0"
```

这表示该字段只允许字符串 `"1.0"`，适合固定输出格式的版本号。

### 7. 模型如何输出

```python
model.model_dump()       # 返回 Python dict
model.model_dump_json()  # 返回 JSON 字符串
```

本题需要写 JSON 文件，所以使用 `model_dump_json(indent=2)`。

### Java 对照速查

| Pydantic | 可以先类比为 |
|---|---|
| `BaseModel` | 带校验和序列化能力的 DTO |
| 字段类型标注 | DTO 字段类型 |
| `Field(default_factory=list)` | 每次构造时 `new ArrayList<>()` |
| `model_validate(dict)` | 把 Map 绑定并校验成 DTO |
| `ValidationError` | 数据绑定或字段校验失败 |
| `model_dump()` | DTO 转 Map |
| `model_dump_json()` | DTO 序列化为 JSON 字符串 |

今天不学习自定义 validator、alias、computed field、JSON Schema 定制、Settings 或 strict mode；看到这些名词先跳过。

## 0～10 分钟：确认依赖

从仓库根目录运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements-dev.txt
.\.venv\Scripts\python.exe -c "import pydantic; print(pydantic.__version__)"
```

Day 6 使用 Pydantic 2，因此序列化方法是 `model_dump()` / `model_dump_json()`，不是旧版示例中的 `dict()` / `json()`。

## 10～45 分钟：完成 TODO 1 和 TODO 2

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

## 45～65 分钟：完成 TODO 5 和 TODO 6

在 `test_day06.py` 中补完两个测试：

- TODO 5：创建两个 `RequirementData()`，只修改第一个实例的 `functions`，证明第二个仍为空。
- TODO 6：把字符串直接传给 `functions`，使用 `pytest.raises(ValidationError)` 证明类型错误被拒绝。

先运行：

```powershell
.\.venv\Scripts\python.exe -m pytest .\Week1\day05\test_day05.py .\Week1\day06\test_day06.py -q
```

初始脚手架预计为 `18 passed, 7 failed`；完成后应为 `25 passed`。

## 65～95 分钟：完成 TODO 3 和 TODO 4

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
.\.venv\Scripts\python.exe -m pytest .\Week1\day05\test_day05.py .\Week1\day06\test_day06.py -q
```

手动运行：

```powershell
.\.venv\Scripts\python.exe -m Week1.day06.cli .\Week1\day06\sample_requirement.txt .\Week1\day06\result.json --verbose
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
