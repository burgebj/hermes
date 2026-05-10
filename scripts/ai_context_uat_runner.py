#!/usr/bin/env python3
"""AI-context Feishu UAT runner.

This is a thin orchestration layer over ``stress_test_feishu_pipeline.py``:

1. Keep the existing UAT inventory, fixtures, sender, log observer, and checks.
2. Let a planner rewrite each case into a more natural user utterance.
3. Run the planned message through Hermes and emit a Markdown/JSON result.

External LLM planning is optional and must be supplied via environment variables;
the runner never prints or persists API keys.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
STRESS_PATH = SCRIPT_DIR / "stress_test_feishu_pipeline.py"


def _load_stress_module():
    spec = importlib.util.spec_from_file_location("stress_test_feishu_pipeline", STRESS_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


stress = _load_stress_module()


def _chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _llm_json(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    timeout: int = 30,
) -> dict[str, Any]:
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        _chat_completions_url(base_url),
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as rsp:
            payload = json.loads(rsp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"planner LLM HTTP {exc.code}: {detail}") from exc

    content = (
        payload.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"planner LLM returned non-JSON content: {content[:200]}") from exc


def _expected_capability(case: dict[str, Any]) -> str:
    if case.get("expect_tool"):
        return str(case["expect_tool"])
    if case.get("expect_tools"):
        return "+".join(str(item) for item in case["expect_tools"])
    if case.get("expect_logs"):
        return "+".join(str(item) for item in case["expect_logs"])
    return str(case.get("static_check") or "")


def _local_plan(case: dict[str, Any], rendered_input: str) -> dict[str, str]:
    identity = str(case.get("identity") or "")
    if identity == "slash" or rendered_input.lstrip().startswith("/"):
        return {"message": rendered_input, "notes": "slash command kept verbatim"}
    if case.get("static_check"):
        return {"message": rendered_input, "notes": "static check kept verbatim"}
    return {
        "message": f"Hermes UAT {case['id']}：{rendered_input}",
        "notes": "local planner preserved the original test intent",
    }


def _llm_plan(
    case: dict[str, Any],
    rendered_input: str,
    *,
    base_url: str,
    api_key: str,
    model: str,
) -> dict[str, str]:
    if str(case.get("identity") or "") == "slash" or rendered_input.lstrip().startswith("/"):
        return {"message": rendered_input, "notes": "slash command kept verbatim"}
    payload = {
        "case_id": case.get("id"),
        "identity": case.get("identity"),
        "original_user_intent": rendered_input,
        "capability_under_test": _expected_capability(case),
        "destructive": bool(case.get("destructive")),
    }
    planned = _llm_json(
        base_url=base_url,
        api_key=api_key,
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You rewrite Feishu UAT test intents into one natural Chinese "
                    "message a real user would send to a bot. Preserve all IDs, "
                    "names, dates, and rendered fixture values exactly. Do not "
                    "mention tool names, UAT internals, expected logs, or this "
                    "testing framework. Return JSON: {\"message\": string, "
                    "\"notes\": string}."
                ),
            },
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
    )
    message = str(planned.get("message") or "").strip()
    if not message:
        raise RuntimeError(f"planner LLM produced empty message for {case.get('id')}")
    return {
        "message": message,
        "notes": str(planned.get("notes") or "llm planner"),
    }


def plan_case(
    case: dict[str, Any],
    rendered_input: str,
    *,
    planner: str,
    base_url: str,
    api_key: str,
    model: str,
) -> dict[str, str]:
    if planner == "local":
        return _local_plan(case, rendered_input)
    if planner == "llm":
        if not (base_url and api_key and model):
            raise RuntimeError(
                "planner=llm requires HERMES_UAT_LLM_BASE_URL, "
                "HERMES_UAT_LLM_API_KEY, and HERMES_UAT_LLM_MODEL"
            )
        return _llm_plan(case, rendered_input, base_url=base_url, api_key=api_key, model=model)
    if planner == "auto" and base_url and api_key and model:
        return _llm_plan(case, rendered_input, base_url=base_url, api_key=api_key, model=model)
    return _local_plan(case, rendered_input)


def _render_or_skip(case: dict[str, Any], fixtures: dict[str, str], allow_placeholders: bool) -> tuple[str | None, dict[str, Any] | None]:
    try:
        return stress.render_case_input(case, fixtures), None
    except stress.MissingFixtureError as exc:
        if allow_placeholders:
            return str(case["input"]), None
        return None, {
            "id": case["id"],
            "passed": False,
            "skipped": True,
            "reason": f"missing fixtures: {', '.join(exc.missing)}",
        }


def classify_red(result: dict[str, Any]) -> str:
    if result.get("passed"):
        return ""
    if result.get("skipped"):
        return str(result.get("reason") or "skipped")
    if result.get("error"):
        return "send_or_static_error"
    if result.get("errors"):
        return "runtime_error"
    if not result.get("route_matched"):
        return "route_missing"
    if not result.get("tool_dispatched"):
        return "expected_tool_not_selected"
    if not result.get("tool_returned"):
        return "tool_no_success_return"
    if not result.get("uat_used"):
        return "uat_identity_unproven"
    return "unknown_red"


def write_markdown_report(
    path: Path,
    *,
    suite: str,
    planner: str,
    route_mode: str,
    user_selector: str,
    chat_id: str,
    results: list[dict[str, Any]],
) -> None:
    passed = sum(1 for item in results if item.get("passed"))
    skipped = sum(1 for item in results if item.get("skipped"))
    failed = sum(1 for item in results if not item.get("passed") and not item.get("skipped"))
    lines = [
        "# Hermes AI Context UAT Report",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- suite: {suite}",
        f"- planner: {planner}",
        f"- route_mode: {route_mode}",
        f"- user: {user_selector}",
        f"- chat_id: {chat_id}",
        f"- summary: {passed}/{len(results)} passed, {skipped} skipped, {failed} failed",
        "",
        "| case | status | identity | expected | route | tool | uat | return | elapsed | red |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for item in results:
        status = "PASS" if item.get("passed") else ("SKIP" if item.get("skipped") else "FAIL")
        route = "profile" if item.get("profile_routed") else ("direct" if item.get("direct_routed") else "-")
        elapsed = item.get("elapsed")
        elapsed_s = f"{float(elapsed):.1f}s" if isinstance(elapsed, (int, float)) else ""
        lines.append(
            "| {case} | {status} | {identity} | {expected} | {route} | {tool} | {uat} | {ret} | {elapsed} | {red} |".format(
                case=item.get("id", ""),
                status=status,
                identity=item.get("identity", ""),
                expected=str(item.get("expected", "")).replace("|", "\\|"),
                route=route,
                tool="Y" if item.get("tool_dispatched") else "-",
                uat="Y" if item.get("uat_used") else "-",
                ret="Y" if item.get("tool_returned") else "-",
                elapsed=elapsed_s,
                red=classify_red(item).replace("|", "\\|"),
            )
        )
    lines.append("")
    lines.append("## Planned Messages")
    lines.append("")
    for item in results:
        planned = str(item.get("planned_input") or "").replace("\n", " ")
        lines.append(f"- {item.get('id')}: {planned}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _filter_cases(cases: list[dict[str, Any]], include_multitenant: bool) -> list[dict[str, Any]]:
    if include_multitenant:
        return cases
    return [case for case in cases if not str(case.get("id") or "").startswith("MT")]


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes Feishu AI-context UAT runner")
    parser.add_argument("--suite", default="smoke", choices=sorted(stress.SUITE_MAP))
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--chat-id", default=os.environ.get("HERMES_FEISHU_TEST_CHAT_ID"))
    parser.add_argument("--uat")
    parser.add_argument("--user", default=os.environ.get("HERMES_FEISHU_TEST_USER", "本人"))
    parser.add_argument("--fixtures")
    parser.add_argument("--set", dest="fixture_set", action="append")
    parser.add_argument("--allow-placeholders", action="store_true")
    parser.add_argument("--allow-destructive", action="store_true")
    parser.add_argument("--strict-identity", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--wait", type=int, default=12)
    parser.add_argument("--gap", type=int, default=4)
    parser.add_argument("--require-card-final", action="store_true")
    parser.add_argument("--max-cases", type=int, default=0)
    parser.add_argument("--include-multitenant", action="store_true")
    parser.add_argument("--route-mode", choices=("direct", "multitenant", "any"), default="direct")
    parser.add_argument("--planner", choices=("local", "llm", "auto"), default="local")
    parser.add_argument("--llm-base-url", default=os.environ.get("HERMES_UAT_LLM_BASE_URL", ""))
    parser.add_argument("--llm-model", default=os.environ.get("HERMES_UAT_LLM_MODEL", ""))
    parser.add_argument("--checkpoint")
    parser.add_argument("--resume-passed", action="store_true")
    parser.add_argument("--report", default="")
    parser.add_argument("--json-report", default="")
    args = parser.parse_args()

    api_key = os.environ.get("HERMES_UAT_LLM_API_KEY", "")
    cases = _filter_cases(stress.select_cases(args.suite, args.case_id), args.include_multitenant)
    if args.max_cases > 0:
        cases = cases[: args.max_cases]
    if not args.chat_id and not args.dry_run and any(not case.get("static_check") for case in cases):
        raise SystemExit("--chat-id is required unless --dry-run is used or all selected cases are static checks.")

    uat_path = Path(args.uat).expanduser() if args.uat else stress.resolve_uat_path(args.user)
    print(f"Loading UAT from {uat_path}")
    uat = stress.load_uat(uat_path, require_valid=not args.dry_run)
    print(f"  open_id: {uat['open_id']}")
    print(f"  chat_id: {args.chat_id or '(dry-run)'}")
    print(f"  suite: {args.suite} ({len(cases)} case(s), include_multitenant={args.include_multitenant})")
    print(f"  planner: {args.planner}")
    print(f"  route_mode: {args.route_mode}")
    print()

    fixtures = stress.load_fixtures(args.fixtures, args.fixture_set)
    checkpoint_path = Path(args.checkpoint).expanduser() if args.checkpoint else None
    passed_ids = stress.passed_checkpoint_ids(checkpoint_path) if checkpoint_path and args.resume_passed else set()
    results: list[dict[str, Any]] = []

    for index, case in enumerate(cases):
        case_id = str(case["id"])
        if case_id in passed_ids:
            result = {"id": case_id, "passed": True, "skipped": True, "reason": "previously passed"}
            print(f"[{case_id}] PASS skip previously passed")
            results.append(result)
            continue

        rendered, skipped = _render_or_skip(case, fixtures, args.allow_placeholders)
        if skipped:
            print(f"[{case_id}] SKIP {skipped['reason']}")
            results.append({**case, **skipped})
            continue
        assert rendered is not None

        try:
            plan = plan_case(
                case,
                rendered,
                planner=args.planner,
                base_url=args.llm_base_url,
                api_key=api_key,
                model=args.llm_model,
            )
        except Exception as exc:
            result = {
                **case,
                "id": case_id,
                "passed": False,
                "error": f"planner_error: {exc}",
                "planned_input": rendered,
            }
            print(f"[{case_id}] FAIL planner: {exc}")
            results.append(result)
            continue

        planned_case = dict(case)
        planned_case["input"] = plan["message"]
        print(f"[{case_id}] planned: {plan['message'][:90]}")

        result = stress.run_case(
            uat,
            args.chat_id or "",
            planned_case,
            args.wait,
            fixtures={},
            allow_placeholders=True,
            allow_destructive=args.allow_destructive,
            strict_identity=args.strict_identity,
            route_mode=args.route_mode,
            dry_run=args.dry_run,
            require_card_final=args.require_card_final,
        )
        result.update(
            {
                "identity": case.get("identity"),
                "original_input": rendered,
                "planned_input": plan["message"],
                "planner_notes": plan.get("notes", ""),
                "route_mode": args.route_mode,
            }
        )
        result["red_reason"] = classify_red(result)
        if checkpoint_path and stress.should_record_checkpoint(result, dry_run=args.dry_run):
            stress.record_checkpoint(checkpoint_path, result)
        results.append(result)
        if index != len(cases) - 1:
            time.sleep(args.gap)

    passed = sum(1 for item in results if item.get("passed"))
    skipped = sum(1 for item in results if item.get("skipped"))
    failed = [item for item in results if not item.get("passed") and not item.get("skipped")]
    print()
    print(f"Summary: {passed}/{len(results)} PASSED, {skipped} SKIPPED, {len(failed)} FAILED")
    if failed:
        for item in failed:
            print(f"  [{item.get('id')}] {classify_red(item)} expected={item.get('expected')}")

    if args.report:
        write_markdown_report(
            Path(args.report).expanduser(),
            suite=args.suite,
            planner=args.planner,
            route_mode=args.route_mode,
            user_selector=args.user,
            chat_id=args.chat_id or "",
            results=results,
        )
        print(f"Markdown report: {args.report}")
    if args.json_report:
        json_path = Path(args.json_report).expanduser()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON report: {args.json_report}")

    if args.dry_run:
        return 0 if not failed else 1
    return 0 if passed == len(results) and not failed else 1


if __name__ == "__main__":
    sys.exit(main())
