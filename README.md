# AI FDE Learning Journey

面向 AI Forward Deployed Engineer / Solution Engineer 方向的公开学习记录。

目标是在 3～6 个月内，沿着 Python、Web API、LLM 应用、RAG、评测和客户交付材料这条主线，完成一个可运行、可验证、可演示的企业 AI PoC。

## 内容导航

- [完整学习路线](./AI-FDE学习路线.md)
- [学习进度](./学习进度.md)
- [Day 1：Python 基础与需求解析](./day01/README.md)
- [Day 2：tuple、重构与异常处理](./day02/README.md)
- [Day 3：dataclass 与 pytest](./day03/README.md)

## 当前技术主线

```text
Python
  → FastAPI + Pydantic + pytest
  → LLM API 与结构化输出
  → RAG、引用与小型评测
  → Streamlit Demo
  → Docker 与客户交付材料
```

## 仓库原则

- 每个学习日包含任务说明、练习代码、自动检查和复盘。
- 只使用自制、公开或脱敏的业务样例。
- 不提交密钥、客户资料、虚拟环境、IDE 配置或机器本地路径。
- 学习成果必须形成代码、测试、文档或可验证输出，不能只停留在阅读课程。

## 运行环境

- Python 3.11
- Windows / PowerShell 示例命令
- 第三方依赖将在实际需要时通过项目依赖文件记录

首次运行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements-dev.txt
```
