# Foundry Chatbot Eval Runs

This project includes a fixed chatbot eval set and a runner script so we can
benchmark prompt/model changes consistently.

## Files

- `backend/data/evals/chat_eval_cases.jsonl`: fixed test cases
- `backend/scripts/run_chat_eval.py`: API runner + scoring + report export
- `backend/data/evals/results/`: generated JSON reports

## Case Format

Each JSONL row must contain:

- `case_id`: unique id
- `user_id`: target employee id for `/api/v1/chat/query`
- `prompt`: user message
- `expect`: deterministic checks

Supported `expect` keys:

- `require_message` (bool, default `true`)
- `require_insights` (bool, default `true`)
- `require_recommendations` (bool)
- `require_course` (bool)
- `require_plan_30_days` (bool)
- `plan_min_items` (int, default `1` when plan is required)
- `require_mentor_email` (bool)
- `must_include_any` (string list)
- `must_include_all` (string list)
- `must_not_include_any` (string list)
- `max_latency_ms` (float)

## Run

Start backend first (for example via Docker Compose).

Use login credentials:

```powershell
$env:EVALUAI_EVAL_AUTH_EMAIL="rrhh.user@scalian.com"
$env:EVALUAI_EVAL_AUTH_PASSWORD="your_password"
python backend/scripts/run_chat_eval.py --base-url http://localhost:8000
```

Or use an existing bearer token:

```powershell
python backend/scripts/run_chat_eval.py --base-url http://localhost:8000 --token "<JWT>"
```

## Exit Code

- `0`: pass rate >= `--fail-under`
- `1`: pass rate < `--fail-under`

Default threshold is `1.0` (all cases must pass).

Example with 80% minimum pass rate:

```powershell
python backend/scripts/run_chat_eval.py --fail-under 0.8
```
