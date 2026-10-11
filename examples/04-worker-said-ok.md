# Example 4: a worker said "ok", and it was not true

> Illustrative. The verifier output below was captured by running `scripts/verify_receipts.py` against a local stand-in for `logctl`, a placeholder for whatever shows your log-rotation policy as the system applies it.

**Request.** "Have the worker change log rotation for the app to keep 7 files, and tell me when it is done."

**What happened.** The agent dispatched the change to a worker. The worker answered `RESULT=ok`.

The tempting report is "Done, the worker changed it." That report rests on one piece of evidence, and that evidence is a self-report (rule 1).

## Ledger

The agent records what the worker said as `said:` and adds a receipt that looks at the live policy:

```markdown
# Ledger: keep 7 days of app logs

- [x] 1. Log rotation for app keeps 7 files
  - receipt: `said:worker-2 reported RESULT=ok`
  - receipt: `cmd:logctl show-policy app | contains=keep=7`
- [ ] 2. Tell the requester
```

## First run

```
$ python3 scripts/verify_receipts.py --ledger receipts.md --reopen
step 1 Log rotation for app keeps 7 files
CLAIM  [1] said:worker-2 reported RESULT=ok -- a self-report is a claim, not evidence; it does not count (via self-report)
FAIL  [2] cmd:logctl show-policy app | contains=keep=7 -- exit 0 but output does not contain the expected text (via logctl)
  -> UNPROVEN: receipt 2 failed
step 2 (open) Tell the requester
  -> open step, not judged
summary: 0 pass, 1 fail; 0 of 1 done step(s) proven
reopened step(s): 1
```

The live policy still says `keep=30`. The worker's `RESULT=ok` meant that its own script exited 0. Perhaps it wrote the change somewhere the rotation daemon does not read. The cause is for the next step; the point is that the claim was false.

`--reopen` rewrote the ledger. Nothing was deleted:

```markdown
# Ledger: keep 7 days of app logs

- ~~[x] 1. Log rotation for app keeps 7 files~~ reopened 2026-10-11: receipt 2 failed
- [ ] 1. Log rotation for app keeps 7 files
  - receipt: `said:worker-2 reported RESULT=ok`
  - receipt: `cmd:logctl show-policy app | contains=keep=7`
- [ ] 2. Tell the requester
```

## After the fix

The agent applies the policy itself, marks step 1 done again, and re-runs the verifier after that last change:

```
$ python3 scripts/verify_receipts.py --ledger receipts.md
step 1 Log rotation for app keeps 7 files
CLAIM  [1] said:worker-2 reported RESULT=ok -- a self-report is a claim, not evidence; it does not count (via self-report)
PASS  [2] cmd:logctl show-policy app | contains=keep=7 -- exit 0, output contains the expected text (via logctl)
  -> PROVEN: 1 receipt(s); behaviour checked through 1 instrument(s): logctl
step 2 (open) Tell the requester
  -> open step, not judged
summary: 1 pass, 0 fail; 1 of 1 done step(s) proven
```

The `said:` line stays. It is part of the record: the worker said ok, and it was wrong.

## Report

> Fixed: the live rotation policy for app now keeps 7 files (`logctl show-policy app`, checked after my change). The worker reported `RESULT=ok` earlier, but the policy was unchanged at that point; I applied it myself. The ledger keeps the struck-through first attempt.

Not: "Done, the worker handled it."
