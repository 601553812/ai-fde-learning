# Day 5 学习记录

## 开始前

- 开始时间：

1. module、package 和 namespace 分别是什么？
module对应一个py文件
package是一个文件夹,来控制同一命名空间
namespace是命名空间,用来指定导入的包或者类
2. 为什么 `python -m Week1.day05.cli` 能让相对导入正常工作？
通过模块生命来加载day05.cli,可以找package上下文
3. 位置参数与 `--verbose` 这种可选参数有什么区别？
位置参数是缺一不可的 可选参数即使没有不影响程序运行
4. DEBUG、INFO、WARNING、ERROR 分别适合记录什么？
debug是调试信息 用来记录程序运行过程 适合在case分叉时记录
info是通常信息 用来记录运行时数据修改前后的变化
warning是警告 用来记录出现意料外的情况 但不至于导致程序崩溃
error是错误 用来记录程序崩溃信息
## 完成后复盘

- 结束时间：3.27
- 实际用时：2h以上

1. pytest 最终结果：
all passed
2. `--help` 是否正常显示：
正常
3. 正常输入、文件不存在、业务校验失败分别返回什么退出码？
正常0 文件不存在1 失败2
4. 今天完成了哪些代码和测试 TODO？
cli.py和test_day05.py
5. `argparse` 相比手动读取 `sys.argv` 解决了什么问题？
规范参数格式 有几个 以什么形式读取
6. logging 相比 `print()` 有什么优势？
可以设置level,方便看日志时找重要日志
7. 为什么业务校验失败仍然需要生成 JSON？
给用户展示哪一部分是有问题的输入资料
8. 明天需要复习的内容：
最好通过我的问题分析一下
9. 日语说明（3～5 句，向使用者介绍 `--help`、详细日志和退出码）：
cliよりプログラムを起動する際に、--helpコマンドを使ったら、説明が出力できます、説明通りご利用ください。
また、プログラムの詳細ログも出力できるような機能追加しました。
プログラムのexit codeも区別して、状況よりコードが変わりますので、そちらよりプログラムの状況が一部把握できました。

## 错题本

### 多种异常的捕获方式

错误写法：

```python
except (FileNotFoundError or UnicodeDecodeError) as exc:
```

`or` 是逻辑运算。异常类对象为真，因此上面的表达式只会得到第一个
`FileNotFoundError`，实际无法捕获 `UnicodeDecodeError`。

正确写法：

```python
except (FileNotFoundError, UnicodeDecodeError) as exc:
```

逗号创建包含两种异常类型的 tuple，`except` 会捕获其中任意一种异常。
