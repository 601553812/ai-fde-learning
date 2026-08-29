# Day 2 — tuple、分支重构与输入异常处理

日期：2026-08-29（日本时间）
计划用时：120 分钟
目标：在 Day 1 解析器的基础上，真正理解 `tuple | None`，减少重复分支，并让程序能处理更真实的日文输入和文件错误。

## 今天只学习这些内容

1. `tuple` 是什么，以及为什么 `classify_line()` 返回 `tuple[str, str] | None`。
2. tuple 解包：`category, content = classified`。
3. 用 `dict` 保存“输入标签 → 输出分类”的固定对应关系。
4. Python 的 `match / case` 与 Java `switch` 的区别，以及为什么本题更适合用 `dict`。
5. `FileNotFoundError` 和 `UnicodeDecodeError` 的基本处理。

今天不要学习类、继承、Web 框架、AI API、异步或 Docker。

## 今天需要完成的 3 个 TODO

| TODO | 方法 | 要做什么 |
|---|---|---|
| TODO 1 | `classify_line()` | 分类单行，支持半角和全角冒号 |
| TODO 2 | `parse_requirement()` | 解析多行，并使用 tuple 解包保存结果 |
| TODO 3 | `run()` | 读取输入文件、生成 JSON，并处理文件异常 |

三个 TODO 都实现并通过 `verify_day02.py`，Day 2 才算完成。

## 完成标准

- `verify_day02.py` 显示 `DAY 2 PASS`。
- 能不用看答案解释：tuple 与 list 的区别、为什么返回值可能是 `None`。
- `parse_requirement()` 中不再为五个分类写五段 `if / elif`。
- 能让程序分别处理英文半角冒号 `:` 和日文全角冒号 `：`。
- 输入文件不存在时，用户看到简短提示，而不是整段错误堆栈。

## 0～20 分钟：补牢 tuple 与 None

先看 Day 1 中的返回类型：

```python
tuple[str, str] | None
```

它表示函数只有两种结果：

- 成功分类：返回两个固定位置的数据，例如 `("functions", "CSV出力")`。
- 空行或注释：返回 `None`，表示“本行没有需要处理的数据”。

tuple 与 list 的关键区别：

- tuple 常用于表示结构固定的一组值，例如这里的“分类 + 内容”。
- list 常用于保存数量会增加或减少的同类数据，例如多条功能。
- tuple 创建后不能修改其中的元素；list 可以 `append()`。

在 `day02_notes.md` 中先回答前 3 题，然后运行：

```powershell
cd 'C:\path\to\ai-fde-learning\day02'
python .\verify_day02.py
```

起始代码尚未完成，因此此时失败是正常现象。

## 20～35 分钟：理解 Python 为什么不用传统 switch

Python 3.10 以后有 `match / case`，但它是“模式匹配”，能力比 Java 的传统 `switch` 更广，并不是所有多分支都应使用它。

```python
def describe_status(status: int) -> str:
    match status:
        case 200:
            return "OK"
        case 404:
            return "Not Found"
        case _:
            return "Other"
```

本题是固定的“一对一映射”，用 `dict` 更直接：只要查到标签对应的分类，不需要写多段逻辑。把你对二者适用场景的理解写入笔记第 4 题。

## 35～70 分钟：完成前两个核心 TODO

打开 `day02_requirement_parser.py`，完成：

1. `classify_line()`：
   - 忽略空行和注释行。
   - 使用 `PREFIX_TO_CATEGORY` 查找四种已知标签。
   - 同时支持 `:` 与 `：`。
   - 已知标签后没有内容时，整行放入 `unknown`。
   - 其他无法识别的行放入 `unknown`。

2. `parse_requirement()`：
   - 调用 `classify_line()`。
   - 返回 `None` 时跳过。
   - 使用 tuple 解包取得 `category` 和 `content`。
   - 直接通过分类名把内容追加到对应 list，不再写五段 `if / elif`。

限制：

- 不安装第三方包。
- 不把样例结果写死。
- 不删除类型标注。
- 不修改 `verify_day02.py` 来绕过检查。

## 70～90 分钟：运行自动检查

```powershell
python .\verify_day02.py
```

如果失败，只处理第一条错误，再重新运行。检查覆盖以下情况：

- 空行与注释。
- 半角和全角冒号。
- 未知行。
- 标签后内容为空。
- tuple 解包后的分类结果。
- 多行解析结果。

## 90～105 分钟：补上文件异常处理

完成 TODO 3：`run(input_path, output_path)`。

输入与返回值：

- `input_path`：需要读取的 UTF-8 日文需求文件路径。
- `output_path`：需要生成的 JSON 文件路径。
- 返回 `0` 表示成功，返回 `1` 表示输入文件读取失败。

正常处理顺序：

1. 使用 `input_path.read_text(encoding="utf-8")` 读取文本。
2. 把文本传给 `parse_requirement()`。
3. 使用 UTF-8 打开 `output_path`，通过 `json.dump()` 写入结果。
4. 写入时使用 `ensure_ascii=False` 和 `indent=2`，保证日文可读。
5. 打印 `Created: {output_path}` 并返回 `0`。

异常处理要求：

- 输入文件不存在时捕获 `FileNotFoundError`，打印 `Input file not found: ...`，返回退出码 `1`。
- 输入文件不是 UTF-8 时捕获 `UnicodeDecodeError`，打印 `Input file is not valid UTF-8: ...`，返回退出码 `1`。
- 发生上述读取错误时不要生成 JSON，也不要显示整段错误堆栈。

手动验证不存在的文件：

```powershell
python .\day02_requirement_parser.py .\not-found.txt .\result.json
$LASTEXITCODE
```

预期：看到一行简短提示，退出码为 `1`，没有长错误堆栈。

再验证正常输入：

```powershell
python .\day02_requirement_parser.py .\sample_requirement.txt .\result.json
Get-Content -Raw -Encoding utf8 .\result.json
python .\verify_day02.py
```

## 105～120 分钟：复盘与日语说明

完成 `day02_notes.md`。最后用日语写 3～5 句，重点说明 Day 2 相比 Day 1 改善了什么，而不是重复程序使用方法。

完成后更新上一级的 `学习进度.md`：填写实际用时、自动检查结果、最难的点和明天需复习内容。

## 提交给我检查时

直接告诉我：

```text
Day 2 完成，请检查
```

我会读取你的实现、运行自动检查，并根据实际情况安排 Day 3。
