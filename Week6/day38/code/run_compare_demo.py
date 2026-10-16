"""已提供：同一固定评测集的检索前后对照，离线零调用。"""

import argparse
import json

from .eval_cases import evaluation_cases, evaluation_chunks
from .retrieval_compare import compare_retrieval


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Day38：固定问题集上的字符对检索改善对照")
    parser.parse_args(argv)
    report = compare_retrieval(evaluation_chunks(), evaluation_cases())
    # 完整生成后一次打印；不创建文件，也不读取账号配置。
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NotImplementedError:
        print("请先完成 bigram_retrieval.py 和 retrieval_compare.py 的 TODO。")
        raise SystemExit(1)
