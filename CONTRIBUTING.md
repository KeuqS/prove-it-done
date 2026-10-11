# Contributing

Thanks for helping. This project is small on purpose: one skill file, one verifier, a few references. Changes that keep it small and keep its claims true are the most welcome.

## Ground rules

- **The verifier stays standard-library Python, 3.9 or later, on Linux, macOS and Windows.** No third-party packages.
- **Every behaviour has a test.** A new receipt kind, option or verdict needs unit tests in `tests/` that would fail without it. A feature with no test is a claim with no receipt.
- **Errors never pass.** Any new check must report an error (timeout, unreachable, missing tool) as FAIL with "a check that errors proves nothing", never as PASS.
- **Never print secrets or command output.** New messages go through `redact()`. If a new kind can carry a credential, add a redaction test for it.
- **`SKILL.md` stays under 10,000 characters**, and each step ends with a criterion someone can check. Longer material goes in `references/`.
- **Example output is real.** If you change what the verifier prints, regenerate the output in `examples/` and `README.md` by running the verifier (stand-ins are fine; say so in the example).
- **No effect claims without data.** Do not add statements about how much the skill reduces false completions unless they come from running the protocol in `evals/run.md`, with the transcripts or a way to reproduce them.

## Development

```
python3 -m unittest discover -s tests -v
python3 scripts/verify_receipts.py --help
```

To score transcripts, see `evals/run.md`.

## Pull requests

- One change per pull request, with a line in `CHANGELOG.md` under "Unreleased".
- Say what you ran to check it, and paste the output. Yes, in this project that is the point.
- New receipt kinds: open an issue first with the claim it proves that the existing kinds cannot.
