# Day 4 — Python 模块、package 与统一 import

日期：2026-08-31（日本时间）
计划用时：120 分钟
目标：把 Day 3 的单文件程序拆分成一个小型 Python package，并使用统一、稳定的 import 路径。

## 为什么今天做这个

Day 3 的测试中曾同时出现两种导入：

```python
from Week1.day03.day03_requirement_parser import empty_result
from day03_requirement_parser import RequirementItem
```

同一个文件以不同模块名加载，项目扩大后可能产生类型身份不同、测试环境与运行环境表现不一致等问题。

Day 4 将代码拆成：

```text
Week1/day04/
├─ __init__.py      对外公开接口
├─ models.py        数据结构
├─ parser.py        文本解析
├─ validation.py    业务校验
├─ cli.py           文件输入输出与命令行入口
└─ test_day04.py    行为测试
```

今天不增加新的业务功能，重点是“改变代码结构后，原有行为仍由测试保证”。

## 今天需要完成的 4 个 TODO

| TODO | 文件 | 内容 |
|---|---|---|
| TODO 1 | `__init__.py` | 统一导出 package 的公共接口 |
| TODO 2 | `parser.py` | 使用 `RequirementItem` 完成单行分类 |
| TODO 3 | `parser.py` | 完成多行解析 |
| TODO 4 | `validation.py` | 返回全部必要分类校验错误 |

完成标准：

- pytest 显示 `12 passed`。
- CLI 能通过 `python -m Week1.day04.cli ...` 运行。
- `test_day04.py` 只从 `day04` 导入公共接口，不混用多种路径。
- 能解释模块、package、`__init__.py` 和相对导入分别解决什么问题。

## 0～15 分钟：确认环境与起始状态

终端先进入仓库根目录，然后执行：

```text
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pytest .\Week1\day04\test_day04.py -q
```

起始状态会在导入阶段失败，这是正常现象，因为 TODO 1 尚未完成。

## 15～35 分钟：理解四个概念

### 模块 module

一个 `.py` 文件就是一个模块，例如：

```text
models.py
parser.py
```

### package

包含 `__init__.py` 的目录可以作为 package 使用。归档后本题的完整 package 名是 `Week1.day04`。

### 相对导入

package 内部可以这样引用同级模块：

```python
from .models import RequirementItem
```

开头的 `.` 表示“当前 package”。

### 公共接口

外部测试不需要知道类究竟定义在哪个子模块，只需要：

```python
from Week1.day04 import RequirementItem
```

`Week1/day04/__init__.py` 负责把需要公开的名字统一导出。

先回答 `day04_notes.md` 的开始前 4 个问题。

## 35～55 分钟：完成 TODO 1

编辑 `Week1/day04/__init__.py`，从三个子模块导入并公开以下名字：

```text
RequirementItem
empty_result
classify_line
parse_requirement
validate_result
```

导入格式示例：

```python
from .models import RequirementItem
```

然后重新运行 pytest。此时应该能够收集测试，并停在尚未实现的解析 TODO。

## 55～85 分钟：完成 TODO 2～4

不要从头重新设计业务规则。参考自己已经通过验收的 Day 3，把实现迁移到对应模块：

- `classify_line()` 和 `parse_requirement()` 放入 `parser.py`。
- `validate_result()` 放入 `validation.py`。
- 数据类已经放在 `models.py`，不要重复定义第二个 `RequirementItem`。

迁移时保持以下规则：

- 空行和注释返回 `None`。
- 支持半角、全角冒号以及内容中的第二个冒号。
- 已知标签缺少合法分隔符时进入 `unknown`。
- 同时缺少两个必要分类时返回两条错误。
- 使用 `item.category` 和 `item.content`，不退回 tuple 下标。

## 85～105 分钟：运行 12 项回归测试

```text
.\.venv\Scripts\python.exe -m pytest .\Week1\day04\test_day04.py -q
```

每次只处理第一个失败，最终必须看到：

```text
12 passed
```

如果出现 `ModuleNotFoundError`，先确认终端位于仓库根目录，不要立即复制文件或修改 `sys.path`。

## 105～115 分钟：以模块方式运行 CLI

PowerShell、CMD 和 Cmder 都可以直接执行这一整行：

```text
.\.venv\Scripts\python.exe -m Week1.day04.cli .\Week1\day04\sample_requirement.txt .\Week1\day04\result.json
```

CMD / Cmder 查看退出码和结果：

```bat
echo %ERRORLEVEL%
type .\Week1\day04\result.json
```

PowerShell 查看退出码和结果：

```powershell
$LASTEXITCODE
Get-Content -Raw -Encoding utf8 .\Week1\day04\result.json
```

这里使用 `python -m Week1.day04.cli`，不要直接执行 `python Week1/day04/cli.py`。前者会以 package 模块方式加载，确保相对导入正常。

## 115～120 分钟：复盘

完成 `day04_notes.md`，重点说明：

- 为什么同一个模块不应以两个名字导入。
- `__init__.py` 为什么不应该复制业务实现。
- 拆分文件后，pytest 如何证明行为没有改变。

完成后告诉我：

```text
Day 4 完成，请检查
```
