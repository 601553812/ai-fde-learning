# AI FDE Learning Journey

面向 AI Forward Deployed Engineer / Solution Engineer 方向的公开学习记录。

目标是在 3～6 个月内，沿着 Python、Web API、LLM 应用、RAG、评测和客户交付材料这条主线，完成一个可运行、可验证、可演示的企业 AI PoC。

## 内容导航

- [完整学习路线](./AI-FDE学习路线.md)
- [学习进度](./学习进度.md)
- [Week 1（Day 1～7）](./Week1/)
  - [Day 1：Python 基础与需求解析](./Week1/day01/README.md)
  - [Day 2：tuple、重构与异常处理](./Week1/day02/README.md)
  - [Day 3：dataclass 与 pytest](./Week1/day03/README.md)
  - [Day 4：Python 模块、package 与统一 import](./Week1/day04/README.md)
  - [Day 5：argparse 与 logging](./Week1/day05/README.md)
  - [Day 6：Pydantic 数据模型与运行时校验](./Week1/day06/README.md)
  - [Day 7：HTTP JSON 客户端与错误边界](./Week1/day07/README.md)
- [Week 2（Day 8～14）](./Week2/README.md)
  - [Day 8：HTTP CLI 单元测试](./Week2/day08/README.md)
  - [Day 9：FastAPI 需求分析接口](./Week2/day09/README.md)
  - [Day 10：API 错误处理与长度边界](./Week2/day10/README.md)
  - [Day 11：可替换分析服务与依赖注入](./Week2/day11/README.md)
  - [Day 12：分析器替换与连续请求巩固](./Week2/day12/README.md)
  - [Day 13：环境变量与安全配置](./Week2/day13/README.md)
  - [Day 14：校验模型返回的 JSON（本地模拟）](./Week2/day14/README.md)
- [Week 3（Day 15～21，从 Day 15 开始）](./Week3/README.md)
  - [Day 15：组织模型请求——提取规则与需求原文](./Week3/day15/README.md)
  - [Day 16：从模型请求到第一次真实调用（进行中）](./Week3/day16/README.md)

## 文件职责

- AGENTS.md：长期协作、教学与验收规则。
- AI-FDE学习路线.md：目标岗位、技术主线与阶段成果。
- 学习进度.md：当前完成状态、每日成果摘要与下一步。
- 每日 README.md：当天知识范围、作业要求与验收方法。
- 每日 dayNN_notes.md：学习者原始回答、实际用时、反馈与复盘。

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
