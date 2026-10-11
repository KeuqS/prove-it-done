# Example 2: a config change

> Illustrative. The verifier output below was captured by running `scripts/verify_receipts.py` against local stand-ins. `appctl` stands for whatever your service offers to show its *effective* settings (an admin endpoint, a CLI, a query against a settings table).

**Request.** "Set the cache TTL to 300 seconds."

**What the agent did.** Edited `etc/app.yaml` to `cache_ttl: 300`, then reloaded the service.

## Claims

1. The running service uses a cache TTL of 300 seconds.

That is a claim about behaviour. "The file says 300" is a different, smaller claim.

## First ledger: config only

```markdown
- [x] 1. Cache TTL is 300 seconds
  - receipt: `file:etc/app.yaml | sha256=35acaddb3c28a7fc73e904f052b2b1be1696e2eabf46ced31351f87b51dd3840 | proves=config`
```

```
$ python3 scripts/verify_receipts.py --ledger receipts.md
step 1 Cache TTL is 300 seconds
PASS  [1] file:etc/app.yaml | sha256=35acaddb3c28a7fc73e904f052b2b1be1696e2eabf46ced31351f87b51dd3840 | proves=config [config] -- sha256 matches (via filesystem)
  -> UNPROVEN: only config receipts passed; a config check is not a behaviour check
summary: 1 pass, 0 fail; 0 of 1 done step(s) proven
```

The hash proves the file holds exactly what was written. It does not prove the service read it. The reload might have failed, another layer (an environment variable, a flag) might override the file, or the service might read a different path.

## Final ledger: config and behaviour

```markdown
- [x] 1. Cache TTL is 300 seconds
  - receipt: `file:etc/app.yaml | sha256=35acaddb3c28a7fc73e904f052b2b1be1696e2eabf46ced31351f87b51dd3840 | proves=config`
  - receipt: `cmd:appctl effective-config cache_ttl | contains=cache_ttl=300`
```

```
$ python3 scripts/verify_receipts.py --ledger receipts.md
step 1 Cache TTL is 300 seconds
PASS  [1] file:etc/app.yaml | sha256=35acaddb3c28a7fc73e904f052b2b1be1696e2eabf46ced31351f87b51dd3840 | proves=config [config] -- sha256 matches (via filesystem)
PASS  [2] cmd:appctl effective-config cache_ttl | contains=cache_ttl=300 -- exit 0, output contains the expected text (via appctl)
  -> PROVEN: 2 receipt(s); behaviour checked through 1 instrument(s): appctl
summary: 2 pass, 0 fail; 1 of 1 done step(s) proven
```

Keep the config receipt: it records *which* file content produced the behaviour, and it fails loudly if someone edits the file later.

## Report

> Done: the service's effective cache TTL is 300 seconds (`appctl effective-config cache_ttl`), and `etc/app.yaml` holds the new setting (sha256 35acaddb3c28...). Both checked after the reload.

If no effective-config instrument exists, the honest report is narrower: "`etc/app.yaml` now says 300 and the reload exited 0. I could not observe the running value, so I have not confirmed the service uses it."
