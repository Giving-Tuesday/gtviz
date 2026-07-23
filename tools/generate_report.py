#!/usr/bin/env python3
"""Generate a comprehensive quality report from CI artifacts.

Reads whatever machine-readable outputs are present and produces a single
Markdown report:

- **Test results** from JUnit XML (``pytest --junitxml``): pass/fail/skip
  counts, pass rate, and a per-file / per-outcome breakdown of failures.
- **Coverage** from ``coverage.xml`` (Cobertura): overall %, and the least-
  covered modules with their missing-line counts.
- **Lint** from ``ruff --output-format=json``: error count by rule code.
- **Visual regression** from ``compare_images`` output if captured.

Usage::

    python tools/generate_report.py \
        --junit junit/*.xml \
        --coverage coverage.xml \
        --ruff ruff.json \
        --out report.md

Every input is optional; missing inputs are reported as "not available" so
the script never crashes a reporting job.
"""

from __future__ import annotations

import argparse
import glob
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def _fmt_pct(num: float, den: float) -> str:
    return f"{(num / den * 100):.1f}%" if den else "n/a"


# --------------------------------------------------------------------------
# JUnit (test results)
# --------------------------------------------------------------------------
def parse_junit(patterns: list[str]) -> dict:
    files: list[str] = []
    for p in patterns:
        files.extend(glob.glob(p))
    if not files:
        return {}

    totals = Counter()
    failures: list[dict] = []
    by_file = defaultdict(lambda: Counter())
    per_env: list[dict] = []

    for f in sorted(set(files)):
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError:
            continue
        suites = root.iter("testsuite")
        env_tests = env_fail = env_err = env_skip = 0
        for suite in suites:
            for case in suite.iter("testcase"):
                totals["tests"] += 1
                env_tests += 1
                classname = case.get("classname", "")
                filekey = classname.split(".")[0] if classname else "unknown"
                fail = case.find("failure")
                err = case.find("error")
                skip = case.find("skipped")
                if fail is not None or err is not None:
                    node = fail if fail is not None else err
                    totals["failed"] += 1
                    env_fail += 1 if fail is not None else 0
                    env_err += 1 if err is not None else 0
                    by_file[filekey]["failed"] += 1
                    failures.append({
                        "test": f"{classname}::{case.get('name')}",
                        "file": filekey,
                        "type": (node.get("type") or "").split(".")[-1] or "failure",
                        "message": (node.get("message") or "").strip().splitlines()[0][:200]
                        if node.get("message") else "",
                        "source": Path(f).stem,
                    })
                elif skip is not None:
                    totals["skipped"] += 1
                    env_skip += 1
                    by_file[filekey]["skipped"] += 1
                else:
                    totals["passed"] += 1
                    by_file[filekey]["passed"] += 1
        per_env.append({
            "source": Path(f).stem, "tests": env_tests,
            "failed": env_fail, "errors": env_err, "skipped": env_skip,
        })

    return {"totals": dict(totals), "failures": failures,
            "by_file": {k: dict(v) for k, v in by_file.items()},
            "per_env": per_env}


# --------------------------------------------------------------------------
# Coverage (Cobertura coverage.xml)
# --------------------------------------------------------------------------
def parse_coverage(path: str | None) -> dict:
    if not path or not Path(path).exists():
        return {}
    root = ET.parse(path).getroot()
    line_rate = float(root.get("line-rate", 0)) * 100
    modules = []
    for cls in root.iter("class"):
        name = cls.get("filename", cls.get("name", "?"))
        lines = cls.find("lines")
        total = covered = 0
        missing = []
        if lines is not None:
            for ln in lines.iter("line"):
                total += 1
                if int(ln.get("hits", 0)) > 0:
                    covered += 1
                else:
                    missing.append(int(ln.get("number", 0)))
        if total:
            modules.append({
                "name": name, "total": total, "covered": covered,
                "pct": covered / total * 100, "missing": len(missing),
            })
    modules.sort(key=lambda m: m["pct"])
    return {"overall": line_rate, "modules": modules}


# --------------------------------------------------------------------------
# Ruff (lint, JSON output)
# --------------------------------------------------------------------------
def parse_ruff(path: str | None) -> dict:
    if not path or not Path(path).exists():
        return {}
    try:
        data = json.loads(Path(path).read_text() or "[]")
    except json.JSONDecodeError:
        return {}
    by_code = Counter()
    by_file = Counter()
    for item in data:
        by_code[item.get("code") or "?"] += 1
        by_file[item.get("filename", "?")] += 1
    return {"total": len(data), "by_code": dict(by_code.most_common()),
            "by_file": dict(by_file.most_common(10))}


# --------------------------------------------------------------------------
# Report assembly
# --------------------------------------------------------------------------
def build(junit: dict, cov: dict, ruff: dict, visual: str | None) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    L: list[str] = ["# gtviz Quality Report\n", f"_Generated {now}_\n"]

    # headline
    t = junit.get("totals", {})
    tests = t.get("tests", 0)
    passed, failed, skipped = t.get("passed", 0), t.get("failed", 0), t.get("skipped", 0)
    overall_ok = failed == 0 and tests > 0
    badge = "PASSING" if overall_ok else ("FAILING" if tests else "NO DATA")
    L.append(f"## Summary: **{badge}**\n")
    L.append("| Metric | Value |")
    L.append("| --- | --- |")
    if tests:
        L.append(f"| Tests run | {tests} |")
        L.append(f"| Passed | {passed} ({_fmt_pct(passed, tests)}) |")
        L.append(f"| Failed | {failed} ({_fmt_pct(failed, tests)}) |")
        L.append(f"| Skipped | {skipped} ({_fmt_pct(skipped, tests)}) |")
    else:
        L.append("| Tests | no JUnit data found |")
    if cov:
        L.append(f"| Line coverage | {cov['overall']:.1f}% |")
    if ruff:
        L.append(f"| Lint findings | {ruff['total']} |")
    L.append("")

    # per-environment (matrix leg) breakdown
    envs = junit.get("per_env", [])
    if len(envs) > 1:
        L.append("## Test results by environment\n")
        L.append("| Source | Tests | Failed | Errors | Skipped |")
        L.append("| --- | ---: | ---: | ---: | ---: |")
        for e in envs:
            L.append(f"| {e['source']} | {e['tests']} | {e['failed']} | "
                     f"{e['errors']} | {e['skipped']} |")
        L.append("")

    # failures
    failures = junit.get("failures", [])
    if failures:
        L.append(f"## Failing tests ({len(failures)})\n")
        by_type = Counter(f["type"] for f in failures)
        L.append("**By failure type:** " +
                 ", ".join(f"`{k}` × {v}" for k, v in by_type.most_common()) + "\n")
        by_file = Counter(f["file"] for f in failures)
        L.append("**By test file:** " +
                 ", ".join(f"`{k}` × {v}" for k, v in by_file.most_common()) + "\n")
        L.append("| Test | Type | Message |")
        L.append("| --- | --- | --- |")
        seen = set()
        for f in failures:
            key = f["test"]
            if key in seen:  # dedupe across matrix legs
                continue
            seen.add(key)
            msg = f["message"].replace("|", "\\|") or "—"
            L.append(f"| `{f['test']}` | {f['type']} | {msg} |")
        L.append("")
    elif tests:
        L.append("## Failing tests\n\nNone — all tests passed.\n")

    # coverage detail
    if cov and cov["modules"]:
        L.append("## Coverage — least-covered modules\n")
        L.append("| Module | Coverage | Covered / Total | Missing lines |")
        L.append("| --- | ---: | ---: | ---: |")
        for m in cov["modules"][:15]:
            flag = " ⚠️" if m["pct"] < 80 else ""
            L.append(f"| {m['name']} | {m['pct']:.0f}%{flag} | "
                     f"{m['covered']}/{m['total']} | {m['missing']} |")
        under = [m for m in cov["modules"] if m["pct"] < 80]
        L.append("")
        L.append(f"_{len(under)} module(s) below 80% coverage._\n")

    # lint detail
    if ruff and ruff["total"]:
        L.append("## Lint findings by rule\n")
        L.append("| Rule | Count |")
        L.append("| --- | ---: |")
        for code, n in ruff["by_code"].items():
            L.append(f"| `{code}` | {n} |")
        L.append("")
    elif ruff is not None and isinstance(ruff, dict) and ruff.get("total") == 0:
        L.append("## Lint\n\nClean — no findings.\n")

    # visual regression
    if visual and Path(visual).exists():
        txt = Path(visual).read_text()
        n_diff = txt.count("[DIFF]")
        n_ok = txt.count("[OK ]")
        L.append("## Visual regression\n")
        L.append(f"- Images compared: {n_ok + n_diff}")
        L.append(f"- Within threshold: {n_ok}")
        L.append(f"- Exceeded threshold: {n_diff}\n")
        if n_diff:
            L.append("<details><summary>Comparison output</summary>\n")
            L.append("```\n" + txt.strip() + "\n```\n</details>\n")

    L.append("---\n")
    L.append("_Report generated by `tools/generate_report.py`. "
             "Test/coverage inputs come from the CI `test` job; lint from the "
             "`lint` job. Missing sections mean that input was not available "
             "to this run._")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--junit", nargs="*", default=[])
    ap.add_argument("--coverage", default=None)
    ap.add_argument("--ruff", default=None)
    ap.add_argument("--visual", default=None)
    ap.add_argument("--out", default="report.md")
    args = ap.parse_args()

    report = build(
        parse_junit(args.junit),
        parse_coverage(args.coverage),
        parse_ruff(args.ruff),
        args.visual,
    )
    Path(args.out).write_text(report, encoding="utf-8")
    print(f"Wrote {args.out} ({len(report)} chars)")


if __name__ == "__main__":
    main()
