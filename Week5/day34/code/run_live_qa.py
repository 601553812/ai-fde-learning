"""已提供：默认只预览；--live 才允许本次单案例发送真实请求。"""

import argparse
import json
from dataclasses import asdict

import httpx

from .cases import QUESTIONS, sample_chunks
from .citations import review_qa_result
from .context import build_context
from .gemini_gateway import DEFAULT_MODEL, GeminiGateway
from .model_client import RecordingGateway
from .qa_prompt import build_qa_request
from .qa_service import answer_question
from .retrieval import retrieve_chunks


def emit(data: dict) -> None:
    # 日文原样输出；只打印本次学习资料和回答，不打印密钥或 HTTP 错误正文。
    print(json.dumps(data, ensure_ascii=False))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Day34：预览或单次 Gemini 资料问答")
    parser.add_argument("--case", choices=QUESTIONS, default="A")
    parser.add_argument("--live", action="store_true", help="发送本案例一次真实请求")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args(argv)
    question = QUESTIONS[args.case]
    chunks = sample_chunks()
    context = build_context(retrieve_chunks(chunks, question, 2), 500)

    if not args.live:
        # 只构造内部请求，不创建 GeminiGateway，也不执行本日的两个 TODO。
        request = build_qa_request(question, context)
        emit({"mode": "preview", "case": args.case, "model": args.model,
              "would_call_model": bool(context.chunks),
              "instructions": request.instructions, "input": json.loads(request.input),
              "context": asdict(context), "gateway_calls": 0})
        return 0

    if not context.chunks:
        # C 直接走已有无资料分支；没有密钥也不需要创建真实网关。
        gateway = RecordingGateway("不应使用")
        result = answer_question(chunks, question, 2, 500, gateway)
        emit({"mode": "live", "case": args.case, "model": args.model,
              **asdict(result), "citation_errors": review_qa_result(result),
              "gateway_calls": 0})
        return 0

    gateway = None
    try:
        gateway = GeminiGateway(model=args.model)
        result = answer_question(chunks, question, 2, 500, gateway)
        emit({"mode": "live", "case": args.case, "model": args.model,
              **asdict(result), "citation_errors": review_qa_result(result),
              "gateway_calls": gateway.request_count})
        return 0  # 内容与编号核查另做；退出 0 不等于回答质量通过。
    except NotImplementedError:
        emit({"error": "unfinished_todo"})
        return 1
    except httpx.HTTPStatusError as exc:
        emit({"error": "http_error", "http_status": exc.response.status_code})
        return 1
    except httpx.RequestError:
        emit({"error": "network_error"})
        return 1
    except ValueError as exc:
        # 只输出应用定义的错误码，不把供应商返回的正文或异常对象打印出来。
        code = str(exc)
        allowed = {"missing_api_key", "invalid_model", "invalid_model_response",
                   "model_not_completed", "missing_model_text"}
        emit({"error": code if code in allowed else "invalid_model_response"})
        return 2 if code in {"missing_api_key", "invalid_model"} else 1
    finally:
        if gateway is not None:
            gateway.close()


if __name__ == "__main__":
    raise SystemExit(main())
