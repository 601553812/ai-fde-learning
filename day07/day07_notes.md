# Day 7 学习记录

## 学习开始

- 开始时间：
- 环境确认：根目录 `.venv` 能否导入 `requests`：

开始时只填写以上两项。下面的问题学完后再回答。

## 完成后复盘

- 结束时间：
- 实际用时：

1. `class RequirementApiError(RuntimeError)` 中，括号里的 `RuntimeError` 表示什么？

2. `-> RequirementData` 表示什么？Python 是否会仅凭它自动检查返回值？

3. `requests.get()`、`Response`、`response.json()` 三者分别是什么？

4. 为什么 HTTP 请求要显式设置 `timeout`？

5. 为什么要在 `response.json()` 之前调用 `raise_for_status()`？

6. JSON 能成功解析以后，为什么还需要 `RequirementData.model_validate()`？

7. 为什么对外统一抛出 `RequirementApiError`，同时又要用 `raise ... from exc` 保留原因？

8. pytest 最终结果：

9. 今天完成了哪些 TODO？

10. 今天最不理解的一个点：

11. 明天需要复习的内容：

12. 日语说明（3～5 句，向客户说明 HTTP 获取、Schema 校验和失败处理）：
