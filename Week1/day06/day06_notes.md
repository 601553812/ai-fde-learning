# Day 6 学习记录

## 学习开始

- 开始时间：18.58

开始时只记录时间，不要求回答尚未学习的概念。先阅读 README 的“今天只学这 7 个知识点”并完成 TODO，概念题统一在学习后回答。

## 完成后复盘

- 结束时间：1.41
- 实际用时：2-3h

1. Python 类型标注会不会在运行时自动拒绝错误类型？Pydantic 补充了什么？
不会。补充了类型检查
2. `dataclass` 和 Pydantic `BaseModel` 的主要职责有什么区别？
类似java的dto 存储数据　BaseModel　还提供运行时绑定、类型校验和序列化。
3. Pydantic Schema 校验与 `validate_result()` 业务校验有什么区别？
~~schema用来检查固定值是否被篡改 用来匹配版本号或者唯一值 检验和等 validate_result用来检查输出的结果是否合法 是否符合预期~~
Pydantic Schema 检查数据结构是否符合契约，包括字段名称、类型、必填项和固定值等约束；validate_result() 检查数据内容是否满足业务要求。
4. 为什么多个模型实例不应该共享同一个默认 list？
引用相同的默认 list 后，如果对 list 进行修改就会导致互相干扰。
5. pytest 最终结果：
all passed
6. `RequirementData` 包含哪些字段？
functions
acceptance_criteria
risks
questions
unknown
7. 哪两种错误数据会产生 `ValidationError`？
字段名正确但实际的类型有问题,例如给str的变量里传了int 初始化了不存在的字段
8. `model_dump()` 和 `model_dump_json()` 分别返回什么类型？
dict和str
9. 正常输入、文件错误、业务校验失败的退出码：
0 1 2
10. 今天完成了哪些 TODO？
1-6都完成了
11. 今天最不理解的一个点：
python的继承方式不像java清晰明了 方法/函数的返回类型看不太懂
12. 明天需要复习的内容：
根据我的问题 你来总结一下我的弱项
13. 日语说明（3～5 句，向使用者解释输出 Schema 与校验错误）：
schema機能については、データがプログラム内部規定仕様通り読み込むかを検証できるような機能です。
仕様通らないデータに対して、プログラムより拒否する。
入力資料よりプログラムに導入する際に、業務に合わないデータがあれば、JSON形で出力されて、記録できるような設計も実装されている。