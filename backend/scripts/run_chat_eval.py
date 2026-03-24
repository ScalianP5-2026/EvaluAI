"""
Run fixed chatbot evaluation cases against the live EvaluAI backend API.

What this script does:
1. Authenticates with /api/v1/auth/login (or uses a provided bearer token)
2. Sends each case prompt to /api/v1/chat/query
3. Applies deterministic pass/fail checks per case
4. Writes a JSON report to backend/data/evals/results/

Usage example:
    python backend/scripts/run_chat_eval.py --base-url http://localhost:8000

Auth options:
- Preferred: set env vars EVALUAI_EVAL_AUTH_EMAIL and EVALUAI_EVAL_AUTH_PASSWORD
- Alternative: pass --token directly
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

EMAIL_REGEX = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b")


class SimpleResponse:
    """Minimal HTTP response wrapper to avoid external deps."""

    def __init__(self, status_code: int, body: bytes, headers: dict[str, Any]) -> None:
        self.status_code = status_code
        self._body = body
        self.headers = headers

    @property
    def text(self) -> str:
        return self._body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.text)


class SimpleHttpClient:
    """Very small POST-only HTTP client for eval runner."""

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    def __enter__(self) -> "SimpleHttpClient":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    def post(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> SimpleResponse:
        data = json.dumps(payload).encode("utf-8")
        req = urllib_request.Request(url=url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        for key, value in (headers or {}).items():
            req.add_header(key, value)

        try:
            with urllib_request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read()
                return SimpleResponse(
                    status_code=getattr(resp, "status", 200),
                    body=body,
                    headers=dict(resp.headers.items()),
                )
        except urllib_error.HTTPError as exc:
            body = exc.read() if exc.fp else b""
            return SimpleResponse(
                status_code=exc.code,
                body=body,
                headers=dict(exc.headers.items()) if exc.headers else {},
            )
        except urllib_error.URLError as exc:
            reason = getattr(exc, "reason", str(exc))
            raise RuntimeError(f"Request failed for {url}: {reason}") from exc


def _load_cases(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Eval dataset not found: {path}")

    cases: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            try:
                case = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_no}: {exc}") from exc

            if "case_id" not in case or "user_id" not in case or "prompt" not in case:
                raise ValueError(
                    f"Case at line {line_no} must contain case_id, user_id, prompt"
                )
            if "expect" not in case or not isinstance(case["expect"], dict):
                case["expect"] = {}
            cases.append(case)

    if not cases:
        raise ValueError(f"Dataset is empty: {path}")
    return cases


def _login_for_token(
    client: SimpleHttpClient,
    base_url: str,
    email: str,
    password: str,
) -> str:
    url = f"{base_url.rstrip('/')}/api/v1/auth/login"
    response = client.post(url, payload={"email": email, "password": password})
    data = _safe_json(response)

    if response.status_code != 200:
        if response.status_code == 401 and password.strip().lower() in {
            "your_password",
            "password",
            "changeme",
            "123456",
        }:
            raise RuntimeError(
                "Login failed (401): placeholder password detected. "
                "Replace EVALUAI_EVAL_AUTH_PASSWORD with the real account password."
            )
        raise RuntimeError(
            "Login failed "
            f"(status={response.status_code}): {data or response.text[:240]}"
        )

    token = (data or {}).get("access_token")
    if not token:
        raise RuntimeError(
            "Login succeeded but no access_token returned. "
            "The account might require first-time password setup."
        )
    return token


def _safe_json(response: SimpleResponse) -> dict[str, Any] | None:
    try:
        parsed = response.json()
        if isinstance(parsed, dict):
            return parsed
        return {"_raw": parsed}
    except Exception:
        return None


def _response_text_for_checks(payload: dict[str, Any] | None) -> str:
    if not payload:
        return ""

    chunks: list[str] = []

    def add(value: Any) -> None:
        if isinstance(value, str) and value.strip():
            chunks.append(value.strip())

    add(payload.get("message"))

    rec = payload.get("recommendations") or {}
    if isinstance(rec, dict):
        add(rec.get("course"))
        add(rec.get("rationale"))
        plan = rec.get("plan_30_days")
        if isinstance(plan, list):
            for item in plan:
                add(item)

    insights = payload.get("insights") or {}
    if isinstance(insights, dict):
        add(insights.get("general"))
        add(insights.get("department"))
        add(insights.get("personal"))

    return _normalize_text("\n".join(chunks))


def _normalize_text(value: str) -> str:
    """Lowercase and strip accents/diacritics for robust keyword checks."""
    normalized = unicodedata.normalize("NFKD", value or "")
    without_marks = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return without_marks.lower()


def _run_case(
    client: SimpleHttpClient,
    base_url: str,
    token: str,
    case: dict[str, Any],
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/chat/query"
    payload = {"user_id": case["user_id"], "message": case["prompt"]}
    headers = {"Authorization": f"Bearer {token}"}

    started = time.perf_counter()
    response = client.post(url, headers=headers, payload=payload)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

    parsed = _safe_json(response)
    expectations = case.get("expect", {})
    checks: list[dict[str, Any]] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        checks.append({"name": name, "pass": bool(condition), "detail": detail})

    check(
        "http_success",
        200 <= response.status_code < 300,
        f"status={response.status_code}",
    )

    text_blob = _response_text_for_checks(parsed)

    # Basic response integrity checks
    require_message = expectations.get("require_message", True)
    if require_message:
        message = (parsed or {}).get("message")
        check("message_present", isinstance(message, str) and bool(message.strip()))

    require_insights = expectations.get("require_insights", True)
    if require_insights:
        insights = (parsed or {}).get("insights")
        condition = (
            isinstance(insights, dict)
            and isinstance(insights.get("general"), str)
            and bool(insights.get("general", "").strip())
            and isinstance(insights.get("department"), str)
            and bool(insights.get("department", "").strip())
            and isinstance(insights.get("personal"), str)
            and bool(insights.get("personal", "").strip())
        )
        check("insights_shape", condition)

    require_recommendations = expectations.get("require_recommendations", False)
    if require_recommendations:
        recommendations = (parsed or {}).get("recommendations")
        check("recommendations_present", isinstance(recommendations, dict))

    if expectations.get("require_course", False):
        recommendations = (parsed or {}).get("recommendations") or {}
        course = recommendations.get("course") if isinstance(recommendations, dict) else None
        check("course_present", isinstance(course, str) and bool(course.strip()))

    if expectations.get("require_plan_30_days", False):
        recommendations = (parsed or {}).get("recommendations") or {}
        plan = recommendations.get("plan_30_days") if isinstance(recommendations, dict) else None
        min_items = int(expectations.get("plan_min_items", 1))
        condition = isinstance(plan, list) and len(plan) >= min_items
        check("plan_30_days_present", condition, f"expected_at_least={min_items}")

    if expectations.get("require_mentor_email", False):
        check("mentor_email_present", bool(EMAIL_REGEX.search(text_blob)))

    must_include_any = [_normalize_text(x) for x in expectations.get("must_include_any", [])]
    if must_include_any:
        condition = any(token in text_blob for token in must_include_any)
        check("must_include_any", condition, f"tokens={must_include_any}")

    must_include_all = [_normalize_text(x) for x in expectations.get("must_include_all", [])]
    if must_include_all:
        condition = all(token in text_blob for token in must_include_all)
        check("must_include_all", condition, f"tokens={must_include_all}")

    must_not_include_any = [_normalize_text(x) for x in expectations.get("must_not_include_any", [])]
    if must_not_include_any:
        condition = all(token not in text_blob for token in must_not_include_any)
        check("must_not_include_any", condition, f"tokens={must_not_include_any}")

    if "max_latency_ms" in expectations:
        max_latency = float(expectations["max_latency_ms"])
        check("latency_budget", elapsed_ms <= max_latency, f"elapsed_ms={elapsed_ms}")

    passed = all(item["pass"] for item in checks)

    return {
        "case_id": case["case_id"],
        "user_id": case["user_id"],
        "prompt": case["prompt"],
        "latency_ms": elapsed_ms,
        "status_code": response.status_code,
        "passed": passed,
        "checks": checks,
        "response": parsed if parsed is not None else {"raw_text": response.text[:3000]},
    }


def _default_dataset_path() -> Path:
    # backend/scripts/run_chat_eval.py -> backend/data/evals/chat_eval_cases.jsonl
    backend_dir = Path(__file__).resolve().parents[1]
    return backend_dir / "data" / "evals" / "chat_eval_cases.jsonl"


def _default_output_path() -> Path:
    backend_dir = Path(__file__).resolve().parents[1]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return backend_dir / "data" / "evals" / "results" / f"chat_eval_{stamp}.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run fixed EvaluAI chatbot eval cases.")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Backend base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--dataset",
        default=str(_default_dataset_path()),
        help="Path to JSONL eval cases file",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional output JSON path. If omitted, uses timestamped default.",
    )
    parser.add_argument(
        "--token",
        default="",
        help="Bearer token. If omitted, script logs in with email/password.",
    )
    parser.add_argument(
        "--auth-email",
        default="",
        help="Auth email for /api/v1/auth/login (or set EVALUAI_EVAL_AUTH_EMAIL).",
    )
    parser.add_argument(
        "--auth-password",
        default="",
        help="Auth password for /api/v1/auth/login (or set EVALUAI_EVAL_AUTH_PASSWORD).",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=60.0,
        help="HTTP timeout in seconds (default: 60)",
    )
    parser.add_argument(
        "--user-id-override",
        default="",
        help=(
            "Force this user_id for all eval cases. Useful when authenticating "
            "as a non-RRHH employee who can only query their own data."
        ),
    )
    parser.add_argument(
        "--fail-under",
        type=float,
        default=1.0,
        help="Minimum pass rate [0.0-1.0] to return exit code 0 (default: 1.0).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_path = Path(args.dataset).resolve()
    output_path = Path(args.output).resolve() if args.output else _default_output_path()

    cases = _load_cases(dataset_path)
    if args.user_id_override.strip():
        override_id = args.user_id_override.strip()
        cases = [{**case, "user_id": override_id} for case in cases]
        print(f"Using --user-id-override={override_id} for all {len(cases)} cases.")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    auth_email = args.auth_email or ""
    auth_password = args.auth_password or ""

    if not args.token and (not auth_email or not auth_password):
        # Late import to avoid optional env reads at module import time.
        import os

        auth_email = auth_email or os.getenv("EVALUAI_EVAL_AUTH_EMAIL", "")
        auth_password = auth_password or os.getenv("EVALUAI_EVAL_AUTH_PASSWORD", "")

    with SimpleHttpClient(timeout=args.timeout_seconds) as client:
        token = args.token
        if not token:
            if not auth_email or not auth_password:
                raise RuntimeError(
                    "Missing auth. Provide --token OR --auth-email/--auth-password "
                    "(or env vars EVALUAI_EVAL_AUTH_EMAIL and EVALUAI_EVAL_AUTH_PASSWORD)."
                )
            token = _login_for_token(
                client=client,
                base_url=args.base_url,
                email=auth_email,
                password=auth_password,
            )

        started = time.perf_counter()
        case_results = [
            _run_case(client=client, base_url=args.base_url, token=token, case=case)
            for case in cases
        ]
        total_elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

    passed = [result for result in case_results if result["passed"]]
    failed = [result for result in case_results if not result["passed"]]
    pass_rate = (len(passed) / len(case_results)) if case_results else 0.0

    latencies = [float(result["latency_ms"]) for result in case_results]
    avg_latency_ms = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "dataset": str(dataset_path),
        "summary": {
            "total_cases": len(case_results),
            "passed_cases": len(passed),
            "failed_cases": len(failed),
            "pass_rate": round(pass_rate, 4),
            "avg_latency_ms": avg_latency_ms,
            "total_runtime_ms": total_elapsed_ms,
            "fail_under": args.fail_under,
        },
        "results": case_results,
    }

    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        f"Eval completed: {len(passed)}/{len(case_results)} passed "
        f"(pass_rate={pass_rate:.2%})."
    )
    print(f"Report: {output_path}")

    if failed:
        print("Failed cases:")
        for result in failed:
            failed_checks = [c for c in result["checks"] if not c["pass"]]
            print(f"- {result['case_id']} (status={result['status_code']})")
            for check in failed_checks:
                detail_suffix = f" | {check['detail']}" if check["detail"] else ""
                print(f"  * {check['name']}{detail_suffix}")

    return 0 if pass_rate >= args.fail_under else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        raise SystemExit(130)
