# Needs-reply eval (10 synthetic threads)

| Version | Correct | False positives | False negatives |
|---|---|---|---|
| v0 (Haiku, prompt after the 2026-10-08 fix) | 10/10 | 0 | 0 |

Caveat: case r06 ("let's discuss after class") reproduces the one false positive seen on real mail, and the prompt was fixed for that pattern before this run. Treat this as a regression test, not an unbiased accuracy estimate. On real mail (7 threads, before the fix): 2 correct needs-reply calls, 1 false positive.
