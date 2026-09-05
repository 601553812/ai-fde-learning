# Week 1 — Python 工程基础（Day 1～7）

本目录收纳第一阶段已经完成并验收的学习内容。

- [Day 1：Python 基础与需求解析](./day01/README.md)
- [Day 2：tuple、重构与异常处理](./day02/README.md)
- [Day 3：dataclass 与 pytest](./day03/README.md)
- [Day 4：Python 模块、package 与统一 import](./day04/README.md)
- [Day 5：argparse 与 logging](./day05/README.md)
- [Day 6：Pydantic 数据模型与运行时校验](./day06/README.md)
- [Day 7：HTTP JSON 客户端与错误边界](./day07/README.md)

从仓库根目录运行 package 或测试时，完整模块名以 `Week1` 开头，例如：

```powershell
.\.venv\Scripts\python.exe -m Week1.day05.cli --help
.\.venv\Scripts\python.exe -m pytest .\Week1\day07\test_day07.py -q
```
