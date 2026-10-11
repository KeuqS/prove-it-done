# Example 3: a published page

> Illustrative. The verifier output below was captured by running `scripts/verify_receipts.py` against a local stand-in server and a scratch git repository, then the host name and URL were replaced with `example.com` placeholders. The error line at the end is unedited: `example.test` is a reserved name that never resolves.

**Request.** "Publish the 'Receipts, not vibes' post."

**What the agent did.** Committed `content/blog/receipts-not-vibes.md` to `main`. The site builds and deploys from `main` on push.

## Claims

1. The post is live at `https://www.example.com/blog/receipts-not-vibes`, with its title on the page.

The commit is how the page gets published. It is not the page being published, so its receipt is tagged `proves=config`.

## Ledger

```markdown
- [x] 1. Post "Receipts, not vibes" is live
  - receipt: `commit:7c00a5a70db4 | repo=. | path=content/blog/receipts-not-vibes.md | branch=main | proves=config`
  - receipt: `http:https://www.example.com/blog/receipts-not-vibes | status=200 | contains=<title>Receipts, not vibes</title>`
```

## First run: right after the push

```
$ python3 scripts/verify_receipts.py --ledger receipts.md --reopen
step 1 Post "Receipts, not vibes" is live
PASS  [1] commit:7c00a5a70db4 | repo=. | path=content/blog/receipts-not-vibes.md | branch=main | proves=config [config] -- commit 7c00a5a70db4 exists, touches content/blog/receipts-not-vibes.md, is on main (via git)
FAIL  [2] http:https://www.example.com/blog/receipts-not-vibes | status=200 | contains=<title>Receipts, not vibes</title> -- HTTP 404, expected 200 (via http:www.example.com)
  -> UNPROVEN: receipt 2 failed
summary: 1 pass, 1 fail; 0 of 1 done step(s) proven
reopened step(s): 1
```

The commit is on `main`, but the site build has not deployed yet. The ledger now reads:

```markdown
- ~~[x] 1. Post "Receipts, not vibes" is live~~ reopened 2026-10-11: receipt 2 failed
- [ ] 1. Post "Receipts, not vibes" is live
  - receipt: `commit:7c00a5a70db4 | repo=. | path=content/blog/receipts-not-vibes.md | branch=main | proves=config`
  - receipt: `http:https://www.example.com/blog/receipts-not-vibes | status=200 | contains=<title>Receipts, not vibes</title>`
```

## Second run: after the build finished

The agent waits for the site's build to report complete, marks the step done again, and re-runs:

```
$ python3 scripts/verify_receipts.py --ledger receipts.md
step 1 Post "Receipts, not vibes" is live
PASS  [1] commit:7c00a5a70db4 | repo=. | path=content/blog/receipts-not-vibes.md | branch=main | proves=config [config] -- commit 7c00a5a70db4 exists, touches content/blog/receipts-not-vibes.md, is on main (via git)
PASS  [2] http:https://www.example.com/blog/receipts-not-vibes | status=200 | contains=<title>Receipts, not vibes</title> -- HTTP 200, body contains the expected text (via http:www.example.com)
  -> PROVEN: 2 receipt(s); behaviour checked through 1 instrument(s): http:www.example.com
summary: 2 pass, 0 fail; 1 of 1 done step(s) proven
```

`contains=` matters here. A 200 alone could be a soft-404 page, a cached older version, or a generic landing page.

## What an error looks like

If the check cannot reach the site at all, that is not a pass and not a fail of the claim. It proves nothing (rule 4):

```
$ python3 scripts/verify_receipts.py 'http:https://www.example.test/blog/receipts-not-vibes | status=200 | timeout=5'
FAIL  [1] http:https://www.example.test/blog/receipts-not-vibes | status=200 | timeout=5 -- error: request failed ([Errno 8] nodename nor servname provided, or not known); a check that errors proves nothing (via http:www.example.test)
  -> UNPROVEN: receipt 1 failed
summary: 0 pass, 1 fail; 0 of 1 done step(s) proven
```

## Report

> Done: "Receipts, not vibes" is live at https://www.example.com/blog/receipts-not-vibes (HTTP 200, title present), checked after the site build finished. Source commit 7c00a5a70db4 on main.
