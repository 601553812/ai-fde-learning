# Day 5 — argparse 与 logging

日期：2026-09-02（日本时间）
计划用时：120 分钟
目标：为需求整理工具增加标准命令行参数解析和分级日志，使它更接近可以交付给其他人使用的 CLI。

## 今天新增什么

Day 4 使用 `sys.argv` 手动判断参数数量。Day 5 改用 Python 标准库：

- `argparse`：定义参数、自动生成帮助、处理缺少参数的错误。
- `logging`：用日志级别区分开发信息、正常信息、业务警告和运行错误。

已有的 dataclass、parser、validation 和 package 结构会直接沿用。今天不要重新修改解析规则，也不引入第三方 CLI 框架。

## 今天需要完成的 6 个 TODO

| TODO | 文件 | 内容 |
|---|---|---|
| TODO 1 | `cli.py` | 创建 `ArgumentParser` 并定义参数 |
| TODO 2 | `cli.py` | 根据 `--verbose` 配置日志级别 |
| TODO 3 | `cli.py` | 使用日志完成读取、校验和 JSON 输出 |
| TODO 4 | `cli.py` | 连接参数解析、日志配置与 `run()` |
| TODO 5 | `test_day05.py` | 测试输入文件不存在 |
| TODO 6 | `test_day05.py` | 测试业务校验失败和退出码 `2` |

完成标准：

- pytest 显示 `17 passed`。
- `--help` 自动显示参数说明并返回 `0`。
- 正常输入生成 UTF-8 JSON 并返回 `0`。
- 输入文件不存在返回 `1`。
- 必要分类缺失时仍生成 JSON，并返回 `2`。
- `--verbose` 开启后能看到 DEBUG 日志。

## 0～15 分钟：记录时间并确认起始状态

在 `day05_notes.md` 写下开始时间，然后从仓库根目录运行：

```text
.\.venv\Scripts\python.exe -m pytest .\Week1\day05\test_day05.py -q --maxfail=1
```

前 12 项 Day 4 回归测试应当通过，CLI 测试会停在 TODO 1。这表示旧功能没有损坏，新功能尚未完成。

## 15～30 分钟：理解 argparse

以前的写法：

```python
if len(sys.argv) != 3:
    print("Usage: ...")
```

问题是帮助文本、参数名称、类型转换和错误处理都要自己写。

`argparse` 的职责是：

```text
命令行字符串
  → 检查参数
  → 转换类型
  → 生成 Namespace
```

例如最终需要得到：

```text
args.input_path   Path
args.output_path  Path
args.verbose      bool
```

`--help` 和参数缺失时的 usage 由 `argparse` 自动处理。

## 30～45 分钟：完成 TODO 1

在 `build_parser()` 中：

1. 创建 `argparse.ArgumentParser`，填写简短 `description`。
2. 添加位置参数 `input_path`，使用 `type=Path`。
3. 添加位置参数 `output_path`，使用 `type=Path`。
4. 添加 `-v` / `--verbose`，使用 `action="store_true"`。
5. 返回 parser 对象。

位置参数没有 `--` 前缀，调用顺序决定含义；可选参数 `--verbose` 可以不提供。

## 45～60 分钟：理解并配置 logging

今天使用四个日志级别：

| 级别 | 本题用途 |
|---|---|
| DEBUG | 正在读取哪个文件、解析出多少项 |
| INFO | 成功创建输出文件 |
| WARNING | 输入合法，但缺少必要业务内容 |
| ERROR | 文件不存在或不是 UTF-8 |

完成 TODO 2：

- `verbose=True` 时使用 `logging.DEBUG`。
- 否则使用 `logging.INFO`。
- 调用 `logging.basicConfig()`。
- 日志格式使用 `%(levelname)s %(name)s: %(message)s`。
- 添加 `force=True`，确保测试或重复运行时配置可以刷新。

## 60～85 分钟：完成 TODO 3 和 TODO 4

### TODO 3：`run()`

处理顺序：

1. DEBUG：记录准备读取的 `input_path`。
2. 用 UTF-8 读取文件。
3. `FileNotFoundError` 或 `UnicodeDecodeError`：记录 ERROR，返回 `1`。
4. 调用解析和业务校验。
5. 每条业务校验错误记录一条 WARNING。
6. 写入包含 `requirements`、`validation_errors` 的 UTF-8 JSON。
7. INFO：记录成功创建的 `output_path`。
8. 没有校验错误返回 `0`，否则返回 `2`。

日志参数优先采用：

```python
LOGGER.info("Created: %s", output_path)
```

这样由 logging 负责最后的字符串格式化。

### TODO 4：`main()`

- 调用 `build_parser().parse_args(argv)`。
- 根据 `args.verbose` 调用 `configure_logging()`。
- 将两个 Path 参数传给 `run()`。
- 返回 `run()` 的退出码。

保留文件末尾的：

```python
raise SystemExit(main())
```

## 85～105 分钟：完成两个 pytest TODO

`test_day05.py` 已提供 15 项测试。你需要补完：

- TODO 5：不存在的输入文件应返回 `1`，且不创建输出。
- TODO 6：只有未知行时应返回 `2`，但仍创建包含两条校验错误的 JSON。

测试可以使用 pytest 提供的 `tmp_path` 创建临时路径，不要在项目目录制造测试垃圾文件。

最终运行：

```text
.\.venv\Scripts\python.exe -m pytest .\Week1\day05\test_day05.py -q
```

预期：

```text
17 passed
```

## 105～115 分钟：手动运行

查看自动帮助：

```text
.\.venv\Scripts\python.exe -m Week1.day05.cli --help
```

运行正常输入并开启详细日志：

```text
.\.venv\Scripts\python.exe -m Week1.day05.cli .\Week1\day05\sample_requirement.txt .\Week1\day05\result.json --verbose
```

CMD / Cmder 查看退出码：

```bat
echo %ERRORLEVEL%
```

PowerShell 查看退出码：

```powershell
$LASTEXITCODE
```

## 115～120 分钟：复盘

填写 `day05_notes.md`。重点说明：

- 位置参数和可选参数的区别。
- 日志与普通 `print()` 的区别。
- 为什么业务校验失败使用退出码 `2`，文件读取失败使用 `1`。

完成后告诉我：

```text
Day 5 完成，请检查
```
