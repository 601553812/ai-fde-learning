# Day 3 — dataclass 与第一组 pytest 测试

日期：2026-08-30（日本时间）
计划用时：120 分钟
目标：使用具名数据结构替代裸 tuple，并第一次亲自编写 pytest 测试。

## 为什么今天学习这些

Day 2 已经能返回：

```python
("functions", "CSV出力")
```

这种 tuple 很轻量，但调用方只能通过位置理解数据。字段继续增加后，`item[0]`、`item[1]` 会越来越难读。

Day 3 改为：

```python
RequirementItem(category="functions", content="CSV出力")
```

`dataclass` 让字段有名字；`frozen=True` 让对象创建后不能修改，保留 tuple 的“固定结果”语义。

今天还会把之前的自制检查脚本升级为 pytest。重点不是记住 pytest 的所有功能，而是掌握：

- 测试文件和测试函数如何命名。
- 用 `assert` 描述期望结果。
- 用 `pytest.raises()` 验证预期异常。
- 一个失败只修一项，再重新运行。

## 今天需要完成的 3 个代码 TODO 和 4 个测试 TODO

| 文件 | TODO | 内容 |
|---|---|---|
| `day03_requirement_parser.py` | TODO 1 | 让 `classify_line()` 返回 `RequirementItem` |
| `day03_requirement_parser.py` | TODO 2 | 使用具名字段完成多行解析 |
| `day03_requirement_parser.py` | TODO 3 | 检查必要分类是否存在 |
| `test_day03.py` | TODO 4～7 | 独立补完 4 个测试 |

完成标准：`pytest` 最终显示 `10 passed`，并且能解释为什么本题使用 dataclass 比裸 tuple 更清楚。

## 0～15 分钟：确认统一环境

本项目从 Day 3 起统一使用仓库根目录的 `.venv`：

```powershell
cd 'C:\path\to\ai-fde-learning'
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pytest --version
```

本机当前已准备好：Python 3.11.15、pytest 9.1.1。

在 PyCharm 中请打开整个仓库根目录，并选择：

```text
<仓库根目录>\.venv\Scripts\python.exe
```

不要再把 `day03` 单独作为新项目打开，这样以后 Day 4、Day 5 不需要重复配置解释器。

## 15～30 分钟：读懂 dataclass

打开 `day03_requirement_parser.py`，观察：

```python
@dataclass(frozen=True)
class RequirementItem:
    category: str
    content: str
```

回答 `day03_notes.md` 的开始前 4 个问题。

注意：

- `RequirementItem` 是类名，通常使用大驼峰命名。
- `category` 和 `content` 是有名字的字段。
- `frozen=True` 表示创建后不能重新赋值。
- dataclass 不负责业务校验；今天仍由普通函数完成校验。

## 30～65 分钟：完成 3 个代码 TODO

### TODO 1：`classify_line()`

规则与 Day 2 相同，但返回值改为 `RequirementItem | None`：

- 空行或注释返回 `None`。
- 支持 `:` 和 `：`。
- 内容中可以再次出现冒号，不能截断后半部分。
- 已知标签但内容为空时，整行作为 `unknown`。
- 无法识别的行也作为 `unknown`。

### TODO 2：`parse_requirement()`

- 逐行调用 `classify_line()`。
- 使用 `if item is None:` 明确处理空结果。
- 通过 `item.category` 和 `item.content` 读取字段。
- 不再使用 `item[0]`、`item[1]` 或 tuple 解包。

### TODO 3：`validate_result()`

返回 `list[str]`：

- 没有任何功能时加入 `At least one function is required`。
- 没有任何验收条件时加入 `At least one acceptance criterion is required`。
- 两项都存在时返回空 list。

## 65～85 分钟：先运行已有测试

```powershell
.\.venv\Scripts\python.exe -m pytest .\day03\test_day03.py -q
```

起始代码会失败，这是正常状态。只处理 pytest 显示的第一项错误。

已有的 6 个测试会帮助你确认：

- dataclass 字段和不可变性。
- 空行、注释、半角冒号和全角冒号。
- 未知行。
- 多行解析结果。

## 85～105 分钟：亲自补完 4 个测试

打开 `test_day03.py`，把 TODO 4～7 中的 `pytest.fail(...)` 替换为实际测试代码。

四个测试分别验证：

1. 内容中再次出现半角冒号时不会被截断。
2. 已知标签后没有内容时进入 `unknown`。
3. 缺少功能时返回对应校验错误。
4. 缺少验收条件时返回对应校验错误。

限制：

- 每个测试必须实际调用被测试函数。
- 使用 `assert` 比较实际值和期望值。
- 不修改生产代码来写死测试结果。
- 不删除或跳过已有测试。

最终必须看到：

```text
10 passed
```

## 105～115 分钟：手动运行 CLI

```powershell
.\.venv\Scripts\python.exe .\day03\day03_requirement_parser.py `
  .\day03\sample_requirement.txt `
  .\day03\result.json
$LASTEXITCODE
Get-Content -Raw -Encoding utf8 .\day03\result.json
```

预期结果：

- 输出 JSON 包含 `requirements` 和 `validation_errors`。
- 当前样例的 `validation_errors` 是空 list。
- 退出码为 `0`。

## 115～120 分钟：复盘

填写 `day03_notes.md`。尤其要用自己的话说明：

- tuple、list、dataclass 分别适合什么数据。
- 为什么测试不能只覆盖正常输入。
- `None` 与空 list 分别表示什么。

完成后直接告诉我：

```text
Day 3 完成，请检查
```
