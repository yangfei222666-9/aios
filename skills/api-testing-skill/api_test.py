"""
API Testing Skill - HTTP 请求测试工具
支持：GET/POST/PUT/DELETE、响应验证、性能测试、批量测试
"""
import sys
import json
import time
import argparse
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode


def send_request(
    url: str,
    method: str = "GET",
    headers: Optional[dict] = None,
    body: Optional[str] = None,
    timeout: int = 30,
) -> dict:
    """发送 HTTP 请求，返回结果字典"""
    headers = headers or {}
    if body and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"

    data = body.encode("utf-8") if body else None
    req = Request(url, data=data, headers=headers, method=method.upper())

    start = time.time()
    try:
        with urlopen(req, timeout=timeout) as resp:
            elapsed = round((time.time() - start) * 1000, 1)
            raw = resp.read()
            try:
                body_out = json.loads(raw)
            except Exception:
                body_out = raw.decode("utf-8", errors="replace")
            return {
                "ok": True,
                "status": resp.status,
                "elapsed_ms": elapsed,
                "headers": dict(resp.headers),
                "body": body_out,
            }
    except HTTPError as e:
        elapsed = round((time.time() - start) * 1000, 1)
        raw = e.read()
        try:
            body_out = json.loads(raw)
        except Exception:
            body_out = raw.decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": e.code,
            "elapsed_ms": elapsed,
            "error": str(e.reason),
            "body": body_out,
        }
    except URLError as e:
        elapsed = round((time.time() - start) * 1000, 1)
        return {
            "ok": False,
            "status": None,
            "elapsed_ms": elapsed,
            "error": f"网络错误: {e.reason}",
            "body": None,
        }
    except TimeoutError:
        return {
            "ok": False,
            "status": None,
            "elapsed_ms": timeout * 1000,
            "error": f"超时（{timeout}s）",
            "body": None,
        }


def perf_test(url: str, method: str, n: int, headers: dict, body: Optional[str], timeout: int) -> dict:
    """简单性能测试：发送 n 次请求，统计耗时"""
    times = []
    errors = 0
    for _ in range(n):
        r = send_request(url, method, headers, body, timeout)
        if r["ok"]:
            times.append(r["elapsed_ms"])
        else:
            errors += 1
    if not times:
        return {"error": "全部请求失败", "errors": errors}
    return {
        "total": n,
        "success": len(times),
        "errors": errors,
        "min_ms": min(times),
        "max_ms": max(times),
        "avg_ms": round(sum(times) / len(times), 1),
    }


def run_suite(suite_file: str, timeout: int) -> None:
    """批量测试：从 JSON 文件读取测试用例"""
    with open(suite_file, encoding="utf-8") as f:
        cases = json.load(f)

    passed = failed = 0
    for case in cases:
        name = case.get("name", case["url"])
        result = send_request(
            case["url"],
            case.get("method", "GET"),
            case.get("headers"),
            json.dumps(case["body"]) if "body" in case else None,
            timeout,
        )
        expect_status = case.get("expect_status")
        ok = result["ok"]
        if expect_status and result["status"] != expect_status:
            ok = False

        status_icon = "✅" if ok else "❌"
        print(f"{status_icon} {name} — {result['status']} ({result['elapsed_ms']}ms)")
        if not ok:
            print(f"   错误: {result.get('error', '状态码不符')}")
            failed += 1
        else:
            passed += 1

    print(f"\n结果: {passed} 通过 / {failed} 失败")


def main():
    parser = argparse.ArgumentParser(description="API 测试工具")
    sub = parser.add_subparsers(dest="cmd")

    # send
    s = sub.add_parser("send", help="发送单个请求")
    s.add_argument("url")
    s.add_argument("--method", "-X", default="GET")
    s.add_argument("--header", "-H", action="append", default=[], metavar="K:V")
    s.add_argument("--body", "-d")
    s.add_argument("--timeout", "-t", type=int, default=30)

    # perf
    p = sub.add_parser("perf", help="性能测试")
    p.add_argument("url")
    p.add_argument("--method", "-X", default="GET")
    p.add_argument("--n", type=int, default=10, help="请求次数")
    p.add_argument("--header", "-H", action="append", default=[], metavar="K:V")
    p.add_argument("--body", "-d")
    p.add_argument("--timeout", "-t", type=int, default=30)

    # suite
    r = sub.add_parser("suite", help="批量测试（JSON 文件）")
    r.add_argument("file", help="测试用例 JSON 文件")
    r.add_argument("--timeout", "-t", type=int, default=30)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    headers = {}
    if hasattr(args, "header"):
        for h in args.header:
            k, _, v = h.partition(":")
            headers[k.strip()] = v.strip()

    if args.cmd == "send":
        result = send_request(args.url, args.method, headers, args.body, args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "perf":
        result = perf_test(args.url, args.method, args.n, headers, args.body, args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "suite":
        run_suite(args.file, args.timeout)


if __name__ == "__main__":
    main()
