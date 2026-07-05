# c-stdlib-alignment-casting-footgun-lab

A tiny local correctness lab about C unsafe casting and byte loading: `memcpy`, unsigned char object-representation views, `uint8_t` byte buffers, `uintptr_t` alignment checks, `_Alignof` markers, malloc/stack alignment observations, manual byte-shift integer loads, endian policy, safe aligned object reads, strict-aliasing/effective-type markers, unsafe cast/deref not-run markers, packed-struct/union portability markers, diagnostic markers, and project-local load-result semantics.

**This is a toy lab, not a production binary parser.**

## Hacker News thread access

The Hacker News thread at https://news.ycombinator.com/item?id=38472174 ("Unaligned accesses in C/C++: what, why and solutions to do it properly") was read via the Hacker News API CLI **before** writing this README. See `hn_thread_evidence.md` for an auditable summary.

## What Hacker News users were actually debating

The linked Quarkslab article is about unaligned integer loads from byte buffers on ARM vs x86, but the HN discussion broadened significantly:

- **Unsafe typed dereferences are the real problem.** Commenters argued that dereferencing a `uint8_t*` through a `uint64_t*` is undefined behavior regardless of the target architecture – "whatever the target architecture is. That it works for the author on x64 just means the compiler didn't break it this time around." The issue is not just alignment; it's aliasing and effective type.

- **Alignment vs strict aliasing.** Multiple commenters focused on the distinction between alignment faults and strict-aliasing/effective-type violations. Even an 8-byte-aligned `uint8_t` buffer can't be dereferenced via `uint64_t*` if the effective type doesn't match – "It isn't UB because the alignment is wrong, it's UB by definition and also the alignment might be wrong."

- **Casting vs dereferencing are different operations.** A key thread theme: aliasing UB is on dereferencing with the wrong dynamic type, not on casting pointers. "If uint8_t is a char type (and invariably it is), then it is fully defined. Similarly, it is perfectly safe to cast a correctly aligned uint8_t* to uint64_t* and dereference it as long as you originally stored an uint64_t into it." The cast alone is not the same as the dereference.

- **uint8_t and unsigned char aliasing.** Commenters noted that `uint8_t` is typically a char type, which matters for aliasing rules. Unsigned char can inspect an object's representation, but the reverse direction (treating arbitrary bytes as a typed object) is not automatically safe.

- **char-style object-representation access is directional.** You can view any object's bytes through `unsigned char`, but you cannot automatically construct a typed object by casting a byte buffer and dereferencing. This directionality came up repeatedly.

- **memcpy came up as a safer route.** Multiple commenters pointed to `memcpy` into a properly declared integer object as the boring portable way to copy object representations. "The right way to cast stuff in memory."

- **Manual byte shifts and endian policy came up.** One commenter argued "the 'multiple loads' solution is IMO correct. It does precisely what it looks like it does, it doesn't rely on any assumptions about how integers are represented, and, IMO best of all, it completely gets rid of the 'native endian' crap." Endianness matters for wire-format parsing, and manual shifts make the policy explicit.

- **x86 success does not prove ARM or portable C behavior.** The article showed ARM faults for unaligned loads; commenters noted that x86 often tolerates unaligned loads (sometimes with performance penalties), but that's local behavior, not portable C. Emscripten was mentioned as a platform where code that worked on x86 and ARM failed.

- **Packed structs and unions came up but need careful scope notes.** The Linux kernel's packed-struct `unaligned()` macro was suggested, but others noted "Uses of pointers to members of packed structs are prone to being miscompiled by GCC." Union type punning was proposed ("Type punning through a union is explicitly supported by the C standard"), with C vs C++ caveats. Neither packed structs nor union punning are presented as a complete universal answer in the thread.

- **-fno-strict-aliasing and restrict came up.** One commenter: "Just make `-fno-strict-aliasing` the default and normalize the abundant use of `restrict`." The existence of `-fno-strict-aliasing` was discussed as an acknowledgment that strict aliasing rules trip real programmers.

- **Sanitizers and -Wcast-align came up as useful diagnostics, not proof.** Commenters recommended `-fsanitize=undefined`, ASan, and `-Wcast-align=strict` as helpful tools to catch these issues, but nobody claimed warnings prove memory safety.

- **C vs C++ rules came up.** `std::bit_cast` (C++20) was mentioned. Union type punning has different portability status in C vs C++. Effective type rules differ.

- **Compiler optimizations and TBAA came up.** Commenters discussed how compilers use type-based alias analysis to optimize, which is why aliasing violations that "work" at -O0 can break at -O2. "Compiler writers have eagerly embraced undefined behavior."

- **"Coding without a net" came up.** One commenter: "if you're playing this kind of game, the compiler cannot type-check what you're doing… You're outside the area covered by the standard. You're coding without a net. But C and C++ are explicitly intended for this kind of situation."

- **SIMD intrinsics alignment footguns.** A detailed comment about `_mm_cvtepi8_epi32()` / PMOVSXBD: the intrinsic takes an `__m128i` value (16-byte aligned) but the instruction with a memory operand imposes no alignment restriction. Casting pointers for intrinsics creates the same alignment/aliasing problems.

- **Stack alignment crashes.** A commenter reported a real crash from calling C code from assembly that didn't honor 16-byte stack alignment – the compiler generated code assuming `%rsp` was 16-byte aligned for vector variables.

- **Atomic unaligned accesses.** Asked about and answered: generally not possible portably; x86 allows it but locks the whole bus; C++ cannot represent an atomic type with less than natural alignment.

- **"This unsafe cast works on my machine" vs "this is defined, portable C."** The thread repeatedly emphasized this distinction. Local x86 behavior, specific compiler versions, specific optimization levels – none of these prove portability.

## What this lab does

47 deterministic synthetic test cases covering:

- unsigned char object-representation views
- uint8_t aliasing portability
- char view directionality
- pointer cast without dereference
- misaligned uint64 dereference (marked not_run)
- wrong effective type dereference (marked not_run)
- aligned object reads
- memcpy loads (u32, u64, roundtrip)
- memmove overlap
- manual little/big endian loads (u16, u32, u64)
- endian policy markers
- uintptr_t alignment detection
- _Alignof queries
- malloc/stack alignment observations
- struct padding / offsetof
- packed struct / union punning context (marked not_required / not_run)
- effective type / strict aliasing markers
- restrict / -fno-strict-aliasing / sanitizer context (marked not_tested)
- cast_align warning context
- x86 / ARM / cross-arch behavior markers (not_tested)
- compiler optimization markers
- atomic unaligned / stack alignment context (not_tested)
- project-local `load_result` wrapper struct
- naive cast/naive endian markers (expected to fail)
- production parser scope markers (not_tested)
- safety caveats

Methods compared: preserve_original_case_baseline, compiler_discovery_checker, c_harness_compile_checker, unsigned_char_view_observer, alignment_policy_observer, memcpy_load_observer, manual_endian_load_observer, memmove_overlap_marker, unsafe_cast_marker, struct_padding_marker, packed_union_portability_marker, diagnostic_scope_marker, architecture_scope_marker, wrapper_policy_marker, copy_size_timing_marker, naive_cast_load_marker, external_arch_truth_not_tested_marker.

**No UB is intentionally executed.** Misaligned typed dereferences, wrong-effective-type dereferences, and similar cases are marked `not_run` / `not_tested` with explanations.

## ISO C vs C++ vs compiler extensions vs local compiler

- **ISO C** exposes: `memcpy`, `memmove`, `memset`, `malloc`/`free`, `stdint.h` types (`uint8_t`, `uint32_t`, `uint64_t`, `uintptr_t`, `size_t`), `_Alignof` / `alignof`, object representation via `unsigned char`, `offsetof`, unions.
- **C++** adds: `std::bit_cast` (C++20), different union punning rules, different effective type rules.
- **Compiler extensions** discussed in HN but NOT required here: `__attribute__((packed))`, `-fno-strict-aliasing`, `-Wcast-align`, sanitizers (`-fsanitize=undefined`, ASan), `restrict`.
- **This lab** uses only ISO C11 standard library features. No compiler extensions required. No sanitizers required. No real ARM/x86 behavior testing. No assembly inspection.

## Compiler availability

The lab searches for a compiler in order: `zig cc`, `cc`, `clang`, `gcc`.

Validated with **zig cc 0.14.1** (clang 19.1.7 backend) – see RESULTS.md for compile command, harness output, and timing. If no compiler is found, this is honestly recorded and the C harness is not validated. **Do NOT install a compiler just to make the lab "pass" – missing compiler = honest skip, not failure.**

## Python policy-observer vs C harness results

The lab distinguishes clearly between:

- **Python policy-observer results**: case generation, expected-observation tracking, method dispatch, scoring, timing, artifact writing – all in Python stdlib, no C required. These run even without a compiler.
- **Compiler-backed C harness results**: `c_alignment_casting_footgun_harness.c` compiled with zig cc (`-std=c11 -Wall -Wextra`), run on generated cases, producing real observations for: unsigned char object-representation views, `_Alignof` queries, malloc/stack alignment, struct padding / `offsetof`, `memcpy` loads (u32/u64 native), manual endian loads (le/be u16/u32/u64), `memmove` overlap, and `load_result` wrapper output. See RESULTS.md "Harness output" section for the exact JSON.
- **Not-run / not-tested cases**: misaligned typed dereferences, wrong effective type dereferences, trap representations, ARM/x86 hardware behavior, sanitizers, fuzzing, static analysis, production parser validation – all explicitly marked `not_tested` / `skip` / `not_run` with reasons. No UB is intentionally executed.
- **Portability claims**: statements about ARM faults, x86 permissive behavior, strict aliasing rules, effective type, C vs C++ union punning, `-fno-strict-aliasing`, sanitizers, etc. come from the HN thread / linked article / ISO C documentation – they are **context, not locally proven** by this toy lab. The lab only proves what the local C harness observed on x86_64/Linux with zig cc 0.14.1.

## Running the lab

```bash
python3 -m py_compile generate_cases.py run_lab.py
python3 generate_cases.py
python3 run_lab.py
```

`run_lab.py` records compiler discovery, compile command, harness output, memcpy/manual-load/alignment/unsigned-char/endian observations, wrapper observations, and no-UB markers.

## Scope: what this lab is NOT

Not a binary parser, not a packet parser, not a file-format parser, not a network protocol parser, not a cryptographic implementation, not a hash benchmark, not a CPU conformance suite, not a compiler conformance suite, not a sanitizer lab, not a fuzzing target, not a static analyzer, not an optimizer benchmark. No real files, no real protocol packets, no real credentials, no downloaded corpora, no external parsers, no ARM emulator, no qemu, no assembly inspection, no real parser generators, no fuzzing frameworks, no static analyzers, no network access.

Use only deterministic synthetic byte buffers generated by the repo itself. Fake labels: fake_bytes, demo_buffer, synthetic_word, toy_packet, etc. No real data.

## Results

See [RESULTS.md](RESULTS.md) for exact commands, summary tables, skip matrix, and honest conclusions. Per-case/per-method data in `results_rows.csv` / `results_rows.json`.

## Verify

See [VERIFY.md](VERIFY.md) for a fresh-clone verification transcript.
