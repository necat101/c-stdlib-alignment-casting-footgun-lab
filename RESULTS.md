# c-stdlib-alignment-casting-footgun-lab — RESULTS

Compiler: zig_cc — clang version 19.1.7 (https://github.com/ziglang/zig-bootstrap de1b01a8c1dddf75a560123ac1c2ab182b4830da)

Compile command: `zig cc -std=c11 -Wall -Wextra -o ./c_harness_bin c_alignment_casting_footgun_harness.c`

C harness compile: OK

Cases: 47
Methods: 17
Result rows: 799

## Scores

- pass_count: 794
- fail_count: 5 — **all 5 are `naive_cast_load_marker` correctly failing on `expected_to_fail_naive=True` cases (footgun baseline working as designed). Zero infrastructure failures.**
- expected_fail_naive: 10
- skip_count: 102

## Python policy-observer vs C harness results

**Python policy-observer** (always runs, no compiler needed):
case generation, expected-observation tracking, method dispatch, scoring, timing, artifact writing – 47 cases × 17 methods = 799 rows.

**Compiler-backed C harness** (zig cc 0.14.1, clang 19.1.7 backend):
`c_alignment_casting_footgun_harness.c` compiled with `-std=c11 -Wall -Wextra`, ran successfully, produced real observations for unsigned char object-rep views, `_Alignof`, malloc/stack alignment, struct padding/`offsetof`, `memcpy` loads, manual endian loads, `memmove` overlap, and `load_result` wrapper – see "Harness output" below.

**Not-run / not-tested**: misaligned typed dereferences, wrong effective type dereferences – marked `not_tested` / `skip` with reasons. No UB intentionally executed.

**Portability claims** about ARM faults, x86 behavior, strict aliasing, effective type, C vs C++ union punning, `-fno-strict-aliasing`, sanitizers, etc. come from the HN thread / linked article / ISO C docs – they are context, **not locally proven** by this toy lab.

## Costs

- cases.json: 31263 bytes
- harness_c: 5279 bytes
- compiled_binary: 2450112 bytes
- compile_elapsed_s: 0.2563
- run_elapsed_s: 0.0074
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
{
  "unsigned_char_view_bytes": [
    240,
    222,
    188,
    154,
    120,
    86,
    52,
    18
  ],
  "alignof_u16": 2,
  "alignof_u32": 4,
  "alignof_u64": 8,
  "malloc_ptr_mod_8": 0,
  "stack_obj_mod_8": 0,
  "struct_pad_size": 12,
  "struct_pad_offset_b": 4,
  "struct_pad_offset_c": 8,
  "memcpy_u64_native": "0x8877665544332211",
  "memcpy_u32_native": "0x12345678",
  "manual_le16": 256,
  "manual_le32": 50462976,
  "manual_le64": "506097522914230528",
  "manual_be16": 1,
  "manual_be32": 66051,
  "manual_be64": "283686952306183",
  "memmove_overlap_ok": true,
  "wrapper_status": 0,
  "wrapper_width": 64,
  "wrapper_aligned": 1,
  "wrapper_endian_policy": 1,
  "wrapper_value": "0x8877665544332211",
  "wrapper_unsafe_deref_rejected": 1
}
```

See results_rows.csv / results_rows.json for per-case/per-method data.
