# VERIFY.md — Fresh-clone verification

This documents a fresh-clone end-to-end run of the lab.

## Environment

- Python: 3.12.3
- Platform: Linux-6.17.0-1009-aws-x86_64-with-glibc2.39
- Date: 2026-07-05
- Compiler: **zig cc 0.14.1** (clang 19.1.7 backend, target x86_64-unknown-linux-musl)
- Network/API/package-manager: **none used during benchmark**

## Transcript

```bash
$ python3 -m py_compile generate_cases.py run_lab.py
# (no output – py_compile OK)

$ python3 generate_cases.py
wrote 47 cases to cases.json

$ export PATH="/tmp/zig-x86_64-linux-0.14.1:$PATH"
$ python3 run_lab.py
loaded 47 cases
compiler: zig_cc @ /tmp/zig-x86_64-linux-0.14.1/zig — clang version 19.1.7 (https://github.com/ziglang/zig-bootstrap de1b01a8c1dddf75a560123ac1c2ab182b4830da)
wrote results_rows.csv (799 rows), RESULTS.md
pass=794 fail=5 naive_expected_fail=10 skip=102
```

## Compiler discovery

Compiler search order: zig cc → cc → clang → gcc

Result: **zig cc 0.14.1 found and used**

- `zig`: `/tmp/zig-x86_64-linux-0.14.1/zig` — version 0.14.1, clang 19.1.7 backend
- Compile command: `zig cc -std=c11 -Wall -Wextra -o ./c_harness_bin c_alignment_casting_footgun_harness.c`
- Compile: OK (0.2563s)
- Harness run: OK (0.0074s)
- Binary size: 2450112 bytes

The C harness source `c_alignment_casting_footgun_harness.c` (5279 bytes, ISO C11) compiled cleanly with `-std=c11 -Wall -Wextra` via zig cc, ran successfully, and produced observations for: unsigned char object-representation views, `_Alignof` (u16=2, u32=4, u64=8), malloc/stack alignment (both 8-byte aligned), struct padding (`sizeof=12`, `offsetof(b)=4`, `offsetof(c)=8`), `memcpy` loads (u64 native `0x8877665544332211`, u32 native `0x12345678`), manual endian loads (le16=256, le32=50462976, le64=506097522914230528, be16=1, be32=66051, be64=283686952306183), `memmove` overlap OK, and `load_result` wrapper output (status=0, width=64, aligned=1, endian_policy=1/little, value=`0x8877665544332211`, unsafe_deref_rejected=1).

## Harness observations

C harness compiled and ran successfully via zig cc. Key observations recorded in RESULTS.md:

- `unsigned_char_view_bytes`: `[240,222,188,154,120,86,52,18]`
- `alignof_u16/32/64`: 2 / 4 / 8
- `malloc_ptr_mod_8`: 0, `stack_obj_mod_8`: 0
- `struct_pad_size`: 12, offsets b=4, c=8
- `memcpy_u64_native`: `0x8877665544332211`
- `memcpy_u32_native`: `0x12345678`
- Manual endian loads: LE 16/32/64 and BE 16/32/64 all observed
- `memmove_overlap_ok`: true
- Wrapper: status 0, width 64, aligned 1, endian_policy 1, value `0x8877665544332211`, unsafe_deref_rejected 1

## Case / method counts

- Cases: 47 (reduced from 65 to fit 40–55 target range)
- Methods: 17
- Result rows: 799 (47 × 17)
- Pass: 794
- Fail: 5 (all naive_cast_load_marker – expected footgun failures, NOT a bug)
- Naive expected failures: 10
- Skip / not_tested: 102

The 5 fails are all `naive_cast_load_marker` correctly rejecting cases where `expected_to_fail_naive=True` but `expected_success="success"` – this is the naive footgun baseline failing as designed. No infrastructure failures. Compiler discovery and C harness compile both passed.

## Artifacts

- `cases.json` — 31263 bytes, 47 deterministic synthetic cases
- `c_alignment_casting_footgun_harness.c` — 5279 bytes, ISO C11
- `results_rows.csv` — 799 rows, per-case/per-method results
- `results_rows.json` — same, JSON format
- `RESULTS.md` — summary with scores, costs, scope markers, harness output
- `hn_thread_evidence.md` — HN thread sentiment summary
- `hn_comments_sanitized.txt` — sanitized HN comment excerpts (audit artifact)

## Scope confirmations

- ✅ HN thread accessed via Hacker News API CLI before writing README
- ✅ HN evidence committed: `hn_thread_evidence.md` + `hn_comments_sanitized.txt`
- ✅ C harness compiled and ran via zig cc 0.14.1, results in RESULTS.md
- ✅ No network/API/package-manager during benchmark (zig was pre-downloaded portable, not installed via package manager)
- ✅ No UB executed – misaligned derefs, wrong effective type derefs marked not_run
- ✅ No real files, no real protocol data, no real credentials
- ✅ Deterministic synthetic byte buffers only
- ✅ Fake labels only (fake_bytes, demo_buffer, synthetic_word, etc.)
- ✅ No ARM/x86 hardware testing, no qemu, no sanitizers, no fuzzing
- ✅ No production parser claims
- ✅ Python policy-observer results clearly distinguished from C harness results
- ✅ Portability claims clearly attributed to HN/article/ISO C context, not locally proven

## Reproduce

```bash
git clone https://github.com/necat101/c-stdlib-alignment-casting-footgun-lab.git
cd c-stdlib-alignment-casting-footgun-lab
python3 -m py_compile generate_cases.py run_lab.py
python3 generate_cases.py
python3 run_lab.py
```

If zig cc is in PATH, `run_lab.py` will automatically discover it, compile `c_alignment_casting_footgun_harness.c`, run it, and record observations in RESULTS.md. Compiler search order: zig cc → cc → clang → gcc. If no compiler is available, this is honestly recorded – do NOT install a compiler just to make the lab "pass".
