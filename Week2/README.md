# Week 2 — API 与模型输出处理（Day 8～14）

本目录归档 Day 8～14。2026-09-15 从根目录迁入；代码导入、测试替换路径和文档命令同步改为 Week2 前缀。学习者原答案、实际用时和结束时间保留；历史步骤与初始失败记录不代表当前未完成项。

- [Day 8：HTTP CLI 单元测试](./day08/README.md)
- [Day 9：FastAPI 需求分析接口](./day09/README.md)
- [Day 10：API 错误处理与长度边界](./day10/README.md)
- [Day 11：可替换分析服务与依赖注入](./day11/README.md)
- [Day 12：分析器替换与连续请求巩固](./day12/README.md)
- [Day 13：环境变量与安全配置](./day13/README.md)
- [Day 14：校验模型返回的 JSON（本地模拟）](./day14/README.md)

从仓库根目录执行：

```text
.\.venv\Scripts\python.exe -m pytest Week2 -q --tb=short
.\.venv\Scripts\python.exe -m Week2.day08.cli --help
.\.venv\Scripts\python.exe -m Week2.day14.demo
.\.venv\Scripts\python.exe -m uvicorn Week2.day14.app:app --host 127.0.0.1 --port 8014
```

Day 11、Day 14 的代码已验收，但部分复盘由助手提供参考答案，不能据此认为概念已独立掌握。进入 [Week 3](../Week3/README.md) 时先按学习进度中的单个案例巩固，再开始新内容。
