# Day 1 — Python 基础与第一个需求整理程序

日期：2026-08-28（日本时间）
计划用时：120 分钟
目标：不使用 AI API，先用普通 Python 把一份日文需求文本整理成结构化 JSON。

## 今天只学习这些内容

Java 与 Python 对照理解：

| Java 概念 | 今天使用的 Python 写法 |
|---|---|
| `String` | `str` |
| `ArrayList<String>` | `list[str]` |
| `HashMap<String, ...>` | `dict[str, ...]` |
| `if / else` | `if / else`，使用缩进表示代码块 |
| `for (String line : lines)` | `for line in lines` |
| 方法 | `def 函数名(...):` |
| `null` | `None` |
| try-with-resources 读取文件 | `with open(...) as file:` |

今天不要学习类、继承、异步、Web 框架、机器学习或 Agent。

## 0～15 分钟：确认环境

先让终端位于仓库根目录，再依次执行：

```powershell
cd .\day01
python --version
python .\day01_requirement_parser.py
```

预期结果：

- 版本显示 `Python 3.11.15`。
- 程序提示还有 `TODO` 或抛出 `NotImplementedError`。这是正常现象，因为作业还没完成。

## 15～35 分钟：读懂已有代码

打开 `day01_requirement_parser.py`，只需要回答下面五个问题：

1. `main()` 从哪里开始运行？
2. `Path` 表示什么？
3. `parse_requirement()` 收到的参数是什么类型？
4. 返回值为什么是 `dict[str, list[str]]`？
5. `json.dump()` 的作用是什么？

把答案写入 `day01_notes.md`。每题 1～2 句话即可。

## 35～75 分钟：完成核心作业

编辑 `day01_requirement_parser.py`，完成两个 TODO。

处理规则：

- 忽略空行和以 `#` 开头的注释行。
- `機能:` 后面的文字放入 `functions`。
- `受入条件:` 后面的文字放入 `acceptance_criteria`。
- `リスク:` 后面的文字放入 `risks`。
- `確認事項:` 后面的文字放入 `questions`。
- 去掉冒号前后无用的空格。
- 遇到不认识的行，不要让程序崩溃；把它放入 `unknown`。

最终 JSON 必须有五个键：

```json
{
  "functions": [],
  "acceptance_criteria": [],
  "risks": [],
  "questions": [],
  "unknown": []
}
```

限制：

- 不允许安装第三方包。
- 不允许直接把预期结果写死在程序里。
- 可以查 Python 官方文档或询问概念，但先自己尝试至少 15 分钟。

## 75～95 分钟：运行和修正

执行：

```powershell
python .\day01_requirement_parser.py
Get-Content -Raw -Encoding utf8 .\result.json
python .\verify_day01.py
```

完成标准：最后一条命令显示：

```text
DAY 1 PASS
```

如果失败，只修复检查程序指出的第一项错误，然后重新运行。

## 95～110 分钟：做两个小改动

在 `sample_requirement.txt` 末尾追加：

```text
機能: CSV形式で結果を出力できること
備考: 初回リリースでは管理画面を対象外とする
```

重新运行程序和自动检查。确认：

- 新功能进入 `functions`。
- `備考:` 行进入 `unknown`。

## 110～120 分钟：复盘

在 `day01_notes.md` 写完：

1. 今天实际用了多少分钟？
2. `list` 和 `dict` 分别解决什么问题？
3. 为什么不能把结果写死？
4. 今天遇到的第一个错误是什么，如何修复？
5. 用日语写 3～5 句，向客户说明这个程序能做什么、不能做什么。

然后更新上一级的 `学习进度.md`，把 Day 1 状态改为“完成”或“部分完成”。不要因为超时而硬做完；120 分钟到点就记录实际进度。

## 提交给我检查时

明天完成后直接告诉我：

```text
Day 1 完成，请检查
```

我会读取代码、运行自动检查、检查你的复盘，再安排 Day 2。不要只把运行结果截图给我，文件保留在这个目录即可。
