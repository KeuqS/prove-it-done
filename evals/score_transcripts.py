#!/usr/bin/env python3
"""score_transcripts.py - score agent transcripts for unproven completion claims.

Each directory given is one arm of an experiment (for example with-skill and
without-skill). Every *.json and *.jsonl file in it is one transcript. Each
transcript is passed to the Agent Trace Clinic CLI (`node cli.mjs FILE --json`),
and its `unproven_completion` findings are counted.

Usage:
  score_transcripts.py --clinic PATH/TO/cli.mjs ARM_DIR [ARM_DIR ...] [--json]

  --clinic PATH   the Clinic's cli.mjs (or set TRACE_CLINIC_CLI)
  --node BIN      node executable (default: node)
  --json          print a JSON report instead of the table

A transcript the Clinic cannot read (exit status other than 0, or output that is
not JSON) is reported as ERROR and is not scored. A scorer that errors proves
nothing, so any ERROR makes the exit status 1.
"""
import json
import os
import subprocess
import sys

DETECTOR = "unproven_completion"


def clinic_runner(node, cli):
    def run(path):
        p = subprocess.run([node, cli, path, "--json"], stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        return p.returncode, p.stdout.decode("utf-8", "replace")
    return run


def score_file(path, runner):
    """Returns a dict: file, status (scored|ERROR), findings (count), evidence (list)."""
    name = os.path.basename(path)
    try:
        rc, out = runner(path)
    except Exception as e:
        return {"file": name, "status": "ERROR", "reason": "runner failed: %s" % e.__class__.__name__}
    if rc != 0:
        return {"file": name, "status": "ERROR", "reason": "clinic exit %d" % rc}
    try:
        report = json.loads(out)
        findings = [f for f in report["findings"] if f.get("id") == DETECTOR]
    except (ValueError, KeyError, TypeError):
        return {"file": name, "status": "ERROR", "reason": "clinic output is not a report"}
    return {"file": name, "status": "scored", "findings": len(findings),
            "evidence": [{"step": f.get("steps", [None])[0], "quote": f.get("evidence", "")} for f in findings]}


def score_arm(directory, runner):
    files = sorted(f for f in os.listdir(directory) if f.endswith((".json", ".jsonl")))
    rows = [score_file(os.path.join(directory, f), runner) for f in files]
    scored = [r for r in rows if r["status"] == "scored"]
    flagged = [r for r in scored if r["findings"] > 0]
    return {
        "arm": os.path.basename(os.path.normpath(directory)),
        "transcripts": len(rows),
        "scored": len(scored),
        "errors": len(rows) - len(scored),
        "flagged": len(flagged),
        "findings": sum(r["findings"] for r in scored),
        "flagged_rate": (len(flagged) / len(scored)) if scored else None,
        "rows": rows,
    }


def render(arms):
    out = []
    for a in arms:
        out.append("arm %s" % a["arm"])
        for r in a["rows"]:
            if r["status"] == "ERROR":
                out.append("  ERROR    %s  (%s)" % (r["file"], r["reason"]))
            else:
                tag = "FLAGGED" if r["findings"] else "clean"
                out.append("  %-8s %s  %d %s finding(s)" % (tag, r["file"], r["findings"], DETECTOR))
                for e in r["evidence"]:
                    out.append("           step %s: %s" % (e["step"], e["quote"]))
    out.append("")
    out.append("%-16s %11s %7s %7s %9s %13s" % ("arm", "transcripts", "scored", "errors", "findings", "flagged rate"))
    for a in arms:
        rate = "n/a" if a["flagged_rate"] is None else "%d/%d (%.0f%%)" % (a["flagged"], a["scored"], 100 * a["flagged_rate"])
        out.append("%-16s %11d %7d %7d %9d %13s" % (a["arm"], a["transcripts"], a["scored"], a["errors"], a["findings"], rate))
    return "\n".join(out)


def main(argv=None, runner=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cli, node, as_json, dirs = os.environ.get("TRACE_CLINIC_CLI"), "node", False, []
    it = iter(argv)
    for a in it:
        if a == "--clinic":
            cli = next(it, None)
        elif a == "--node":
            node = next(it, "node")
        elif a == "--json":
            as_json = True
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            dirs.append(a)
    if not dirs or (runner is None and not cli):
        print(__doc__, file=sys.stderr)
        return 2
    for d in dirs:
        if not os.path.isdir(d):
            print("not a directory: %s" % d, file=sys.stderr)
            return 2
    runner = runner or clinic_runner(node, cli)
    arms = [score_arm(d, runner) for d in dirs]
    print(json.dumps(arms, indent=2) if as_json else render(arms))
    return 1 if any(a["errors"] for a in arms) else 0


if __name__ == "__main__":
    sys.exit(main())
