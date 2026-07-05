# c-stdlib-alignment-casting-footgun-lab — RESULTS

Compiler: none — n/a

Compile command: ``

C harness compile: FAILED

Cases: 65
Methods: 17
Result rows: 1105

## Scores

- pass_count: 1100
- fail_count: 5
- expected_fail_naive: 12
- skip_count: 306

## Costs

- cases.json: 43482 bytes
- harness_c: 5279 bytes
- compiled_binary: 0 bytes
- compile_elapsed_s: 0.0000
- run_elapsed_s: 0.0000
- python: 3.12.3
- platform: Linux-6.17.0-1009-aws-x86_64-with-glibc2.39

## Scope markers

- undefined-behavior-not-run: YES — misaligned typed derefs, wrong effective type derefs marked not_run
- alignment-casting-scope: C stdlib memcpy, unsigned char object rep, uintptr_t alignment, manual endian loads
- architecture-not-tested: YES — ARM, x86 alignment checking, atomics, stack alignment crashes not reproduced
- portability-not-tested: trap representations, cross-arch behavior marked not_tested
- production-parser-not-tested: YES — toy lab only
- HN-thread-access: YES — via Hacker News API CLI
- network/API/package-manager: NONE during benchmark — local only

## Harness output

```json
{}
```

See results_rows.csv / results_rows.json for per-case/per-method data.
