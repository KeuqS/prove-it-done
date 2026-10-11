# Example 1: a deploy

> Illustrative. The verifier output below was captured by running `scripts/verify_receipts.py` against local stand-ins, then the host names were replaced with `example.com` placeholders. The format is exactly what the verifier prints.

**Request.** "Deploy web 2.1.0 to staging and confirm it is live."

**What the agent had.** The deploy tool answered `ok: rollout started for web@2.1.0`. That is the tool reporting on itself (rule 1). It says the rollout *started*, which is not a claim that staging serves 2.1.0.

## Claims

1. Staging runs web 2.1.0, meaning the version endpoint answers 2.1.0 and the rollout has finished.

## First ledger

The first draft had the tool's report, one HTTP check, and the image tag from the deployment spec:

```markdown
- [x] 1. Staging runs web 2.1.0
  - receipt: `said:deploy tool returned "ok: rollout started for web@2.1.0"`
  - receipt: `http:https://staging.example.com/version | status=200 | contains="version":"2.1.0"`
  - receipt: `cmd:kubectl -n staging get deploy web -o jsonpath={..image} | contains=web:2.1.0 | proves=config`
```

The image tag is the *desired* state, so it is tagged `proves=config` (rule 3). This is a production deploy, so the agent asks for two independent instruments:

```
$ python3 scripts/verify_receipts.py --ledger receipts.md --min-instruments 2
step 1 Staging runs web 2.1.0
CLAIM  [1] said:deploy tool returned "ok: rollout started for web@2.1.0" -- a self-report is a claim, not evidence; it does not count (via self-report)
PASS  [2] http:https://staging.example.com/version | status=200 | contains="version":"2.1.0" -- HTTP 200, body contains the expected text (via http:staging.example.com)
PASS  [3] cmd:kubectl -n staging get deploy web -o jsonpath={..image} | contains=web:2.1.0 | proves=config [config] -- exit 0, output contains the expected text (via kubectl)
  -> UNPROVEN: 1 behaviour receipt(s) through 1 instrument(s) (http:staging.example.com); need 2 distinct
summary: 2 pass, 0 fail; 0 of 1 done step(s) proven
```

Only one behaviour instrument. One answer from the version endpoint could come from a single new pod while the rest still run 2.0.9.

## Final ledger

The agent adds a behaviour check through a second instrument: the orchestrator's own rollout status.

```markdown
- [x] 1. Staging runs web 2.1.0
  - receipt: `said:deploy tool returned "ok: rollout started for web@2.1.0"`
  - receipt: `http:https://staging.example.com/version | status=200 | contains="version":"2.1.0"`
  - receipt: `cmd:kubectl -n staging rollout status deploy/web --timeout=60s | contains=successfully rolled out`
  - receipt: `cmd:kubectl -n staging get deploy web -o jsonpath={..image} | contains=web:2.1.0 | proves=config`
```

```
$ python3 scripts/verify_receipts.py --ledger receipts.md --min-instruments 2
step 1 Staging runs web 2.1.0
CLAIM  [1] said:deploy tool returned "ok: rollout started for web@2.1.0" -- a self-report is a claim, not evidence; it does not count (via self-report)
PASS  [2] http:https://staging.example.com/version | status=200 | contains="version":"2.1.0" -- HTTP 200, body contains the expected text (via http:staging.example.com)
PASS  [3] cmd:kubectl -n staging rollout status deploy/web --timeout=60s | contains=successfully rolled out -- exit 0, output contains the expected text (via kubectl)
PASS  [4] cmd:kubectl -n staging get deploy web -o jsonpath={..image} | contains=web:2.1.0 | proves=config [config] -- exit 0, output contains the expected text (via kubectl)
  -> PROVEN: 3 receipt(s); behaviour checked through 2 instrument(s): http:staging.example.com, kubectl
summary: 3 pass, 0 fail; 1 of 1 done step(s) proven
```

## Report

> Done: staging runs web 2.1.0. `https://staging.example.com/version` returns 2.1.0 (HTTP 200), and `kubectl rollout status` reports the rollout complete. Both checks ran after the deploy.

Not: "Deployed 2.1.0, the tool said ok."
