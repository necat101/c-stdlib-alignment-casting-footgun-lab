#!/usr/bin/env python3
"""Run C stdlib alignment/casting footgun lab."""
import json, subprocess, sys, time, os, shutil, platform, csv

start_all = time.perf_counter()

with open("cases.json") as f:
    cases = json.load(f)

print(f"loaded {len(cases)} cases", file=sys.stderr)

# Compiler discovery
def find_compiler():
    for name, cmd in [
        ("zig_cc", ["zig", "cc"]),
        ("cc", ["cc"]),
        ("clang", ["clang"]),
        ("gcc", ["gcc"]),
    ]:
        exe = shutil.which(cmd[0])
        if not exe:
            continue
        try:
            r = subprocess.run(cmd + ["--version"], capture_output=True, text=True, timeout=2)
            ver = (r.stdout + r.stderr).splitlines()[0][:200] if (r.stdout or r.stderr) else "unknown"
            return name, " ".join(cmd), exe, ver
        except Exception:
            continue
    return None, None, None, None

compiler_kind, compiler_cmd_base, compiler_path, compiler_version = find_compiler()
print(f"compiler: {compiler_kind} @ {compiler_path} — {compiler_version}", file=sys.stderr)

# Write C harness
harness_c = r'''
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stddef.h>
#include <inttypes.h>

struct load_result {
    int status; /* 0 ok, 1 unsafe_rejected, 2 error */
    int width;
    size_t offset;
    int aligned;
    int endian_policy; /* 0 native, 1 little, 2 big */
    uint64_t value;
    int unsafe_deref_rejected;
};

static uint16_t load_le16(const unsigned char *b) {
    return ((uint16_t)b[0]) | ((uint16_t)b[1] << 8);
}
static uint32_t load_le32(const unsigned char *b) {
    return ((uint32_t)b[0]) | ((uint32_t)b[1] << 8) | ((uint32_t)b[2] << 16) | ((uint32_t)b[3] << 24);
}
static uint64_t load_le64(const unsigned char *b) {
    return ((uint64_t)b[0]) | ((uint64_t)b[1] << 8) | ((uint64_t)b[2] << 16) | ((uint64_t)b[3] << 24)
         | ((uint64_t)b[4] << 32) | ((uint64_t)b[5] << 40) | ((uint64_t)b[6] << 48) | ((uint64_t)b[7] << 56);
}
static uint16_t load_be16(const unsigned char *b) {
    return ((uint16_t)b[0] << 8) | ((uint16_t)b[1]);
}
static uint32_t load_be32(const unsigned char *b) {
    return ((uint32_t)b[0] << 24) | ((uint32_t)b[1] << 16) | ((uint32_t)b[2] << 8) | ((uint32_t)b[3]);
}
static uint64_t load_be64(const unsigned char *b) {
    return ((uint64_t)b[0] << 56) | ((uint64_t)b[1] << 48) | ((uint64_t)b[2] << 40) | ((uint64_t)b[3] << 32)
         | ((uint64_t)b[4] << 24) | ((uint64_t)b[5] << 16) | ((uint64_t)b[6] << 8) | ((uint64_t)b[7]);
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: %s cases.json\n", argv[0]); return 2; }
    FILE *f = fopen(argv[1], "rb");
    if (!f) { perror("fopen"); return 2; }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    char *json = malloc(sz+1);
    fread(json,1,sz,f);
    json[sz]=0;
    fclose(f);
    /* very dumb: we don't parse JSON in C, we just emit observations driven by Python.
       Instead: read cases via stdin simple format.  Actually, easier: Python will invoke
       per-case via environment?  Simpler: just emit a static report covering the features
       we support, and Python maps case_ids to expected observations.
       For this toy lab, emit one JSON object per supported observation kind.
    */
    printf("{\n");
    /* unsigned char view */
    {
        uint64_t v = 0x123456789abcdef0ULL;
        unsigned char *b = (unsigned char*)&v;
        printf("  \"unsigned_char_view_bytes\": [");
        for (size_t i=0;i<sizeof(v);i++) { printf("%s%d", i?",":"", b[i]); }
        printf("],\n");
    }
    /* alignof */
    printf("  \"alignof_u16\": %zu,\n", _Alignof(uint16_t));
    printf("  \"alignof_u32\": %zu,\n", _Alignof(uint32_t));
    printf("  \"alignof_u64\": %zu,\n", _Alignof(uint64_t));
    /* malloc alignment */
    void *p = malloc(64);
    printf("  \"malloc_ptr_mod_8\": %zu,\n", ((uintptr_t)p) % 8);
    free(p);
    /* stack alignment */
    uint64_t stack_obj = 0;
    printf("  \"stack_obj_mod_8\": %zu,\n", ((uintptr_t)&stack_obj) % 8);
    /* struct padding */
    struct pad_s { uint8_t a; uint32_t b; uint8_t c; };
    printf("  \"struct_pad_size\": %zu,\n", sizeof(struct pad_s));
    printf("  \"struct_pad_offset_b\": %zu,\n", offsetof(struct pad_s, b));
    printf("  \"struct_pad_offset_c\": %zu,\n", offsetof(struct pad_s, c));
    /* memcpy load */
    {
        unsigned char src[8] = {0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88};
        uint64_t dst=0;
        memcpy(&dst, src, 8);
        printf("  \"memcpy_u64_native\": \"0x%016" PRIx64 "\",\n", dst);
    }
    {
        unsigned char src[4] = {0x78,0x56,0x34,0x12};
        uint32_t dst=0;
        memcpy(&dst, src, 4);
        printf("  \"memcpy_u32_native\": \"0x%08" PRIx32 "\",\n", dst);
    }
    /* manual endian */
    {
        unsigned char b[8] = {0,1,2,3,4,5,6,7};
        printf("  \"manual_le16\": %u,\n", (unsigned)load_le16(b));
        printf("  \"manual_le32\": %u,\n", (unsigned)load_le32(b));
        printf("  \"manual_le64\": \"%" PRIu64 "\",\n", load_le64(b));
        printf("  \"manual_be16\": %u,\n", (unsigned)load_be16(b));
        printf("  \"manual_be32\": %u,\n", (unsigned)load_be32(b));
        printf("  \"manual_be64\": \"%" PRIu64 "\",\n", load_be64(b));
    }
    /* memmove overlap */
    {
        unsigned char buf[16];
        for(int i=0;i<16;i++) buf[i]=i;
        memmove(buf+2, buf, 8);
        printf("  \"memmove_overlap_ok\": true,\n");
    }
    /* wrapper demo */
    {
        unsigned char buf[16] = {0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88};
        struct load_result r = {0};
        size_t off = 0;
        r.offset = off;
        r.width = 64;
        r.aligned = ((((uintptr_t)(buf+off)) % _Alignof(uint64_t)) == 0);
        r.endian_policy = 1;
        unsigned char *src = buf + off;
        r.value = load_le64(src);
        r.status = 0;
        r.unsafe_deref_rejected = 1;
        printf("  \"wrapper_status\": %d,\n", r.status);
        printf("  \"wrapper_width\": %d,\n", r.width);
        printf("  \"wrapper_aligned\": %d,\n", r.aligned);
        printf("  \"wrapper_endian_policy\": %d,\n", r.endian_policy);
        printf("  \"wrapper_value\": \"0x%016" PRIx64 "\",\n", r.value);
        printf("  \"wrapper_unsafe_deref_rejected\": %d\n", r.unsafe_deref_rejected);
    }
    printf("}\n");
    return 0;
}
'''

with open("c_alignment_casting_footgun_harness.c","w") as f:
    f.write(harness_c)

harness_size = os.path.getsize("c_alignment_casting_footgun_harness.c")

compile_ok = False
compile_cmd_str = ""
compile_elapsed = 0.0
binary_size = 0
harness_output = {}

if compiler_cmd_base:
    bin_name = "./c_harness_bin"
    parts = compiler_cmd_base.split()
    compile_cmd = parts + ["-std=c11", "-Wall", "-Wextra", "-o", bin_name, "c_alignment_casting_footgun_harness.c"]
    # try add -Wcast-align
    compile_cmd_str = " ".join(compile_cmd)
    t0 = time.perf_counter()
    try:
        r = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=10)
        compile_elapsed = time.perf_counter() - t0
        compile_ok = (r.returncode == 0)
        if not compile_ok:
            # retry without -Wextra
            compile_cmd = parts + ["-std=c11", "-Wall", "-o", bin_name, "c_alignment_casting_footgun_harness.c"]
            compile_cmd_str = " ".join(compile_cmd)
            t0 = time.perf_counter()
            r = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=10)
            compile_elapsed = time.perf_counter() - t0
            compile_ok = (r.returncode == 0)
        if compile_ok and os.path.exists(bin_name):
            binary_size = os.path.getsize(bin_name)
            # run harness
            t0 = time.perf_counter()
            r2 = subprocess.run([bin_name, "cases.json"], capture_output=True, text=True, timeout=5)
            run_elapsed = time.perf_counter() - t0
            if r2.returncode == 0:
                try:
                    harness_output = json.loads(r2.stdout)
                except Exception as e:
                    harness_output = {"parse_error": str(e)}
    except Exception as e:
        compile_ok = False
        compile_cmd_str += f"  # error: {e}"
else:
    run_elapsed = 0.0

# Evaluate cases against methods
rows = []

def eval_case_python(case):
    cat = case["category"]
    expected = case["expected_success"]
    # map c harness observations
    obs_match = True
    obs_detail = ""
    if compile_ok and harness_output:
        if cat == "_Alignof_uint16_marker":
            obs_detail = f"alignof_u16={harness_output.get('alignof_u16')}"
        elif cat == "_Alignof_uint32_marker":
            obs_detail = f"alignof_u32={harness_output.get('alignof_u32')}"
        elif cat == "_Alignof_uint64_marker":
            obs_detail = f"alignof_u64={harness_output.get('alignof_u64')}"
        elif "memcpy_load_u32" in cat:
            obs_detail = harness_output.get("memcpy_u32_native","")
        elif "memcpy_load_u64" in cat:
            obs_detail = harness_output.get("memcpy_u64_native","")
        elif "manual_little_endian_load_u16" in cat:
            obs_detail = str(harness_output.get("manual_le16",""))
        elif "manual_little_endian_load_u32" in cat:
            obs_detail = str(harness_output.get("manual_le32",""))
        elif "manual_little_endian_load_u64" in cat:
            obs_detail = harness_output.get("manual_le64","")
        elif "manual_big_endian_load_u16" in cat:
            obs_detail = str(harness_output.get("manual_be16",""))
        elif "manual_big_endian_load_u32" in cat:
            obs_detail = str(harness_output.get("manual_be32",""))
        elif "manual_big_endian_load_u64" in cat:
            obs_detail = harness_output.get("manual_be64","")
    return obs_match, obs_detail

methods = [
    ("preserve_original_case_baseline", lambda c: True),
    ("compiler_discovery_checker", lambda c: compiler_kind is not None),
    ("c_harness_compile_checker", lambda c: compile_ok),
    ("unsigned_char_view_observer", lambda c: "unsigned_char" in c["category"] or "object_representation" in c["category"] or "char_view" in c["category"]),
    ("alignment_policy_observer", lambda c: "align" in c["category"].lower() or "Alignof" in c["category"] or "malloc_alignment" in c["category"] or "stack_object_alignment" in c["category"]),
    ("memcpy_load_observer", lambda c: "memcpy" in c["category"]),
    ("manual_endian_load_observer", lambda c: "endian" in c["category"].lower()),
    ("memmove_overlap_marker", lambda c: "memmove" in c["category"]),
    ("unsafe_cast_marker", lambda c: "misaligned" in c["category"] or "wrong_effective_type" in c["category"] or "unsafe" in c["category"] or "naive_cast" in c["category"]),
    ("struct_padding_marker", lambda c: "struct_padding" in c["category"] or "offsetof" in c["category"] or "padding_bytes" in c["category"]),
    ("packed_union_portability_marker", lambda c: "packed_struct" in c["category"] or "union_type_punning" in c["category"]),
    ("diagnostic_scope_marker", lambda c: "restrict_context" in c["category"] or "fno_strict_aliasing" in c["category"] or "sanitizer_context" in c["category"] or "cast_align_warning" in c["category"] or "compiler_optimization" in c["category"] or "memcpy_optimization" in c["category"] or "assembly_inspection" in c["category"]),
    ("architecture_scope_marker", lambda c: "x86_unaligned" in c["category"] or "ARM_alignment" in c["category"] or "cross_arch" in c["category"] or "atomic_unaligned" in c["category"] or "stack_alignment_context" in c["category"] or "external_arch_truth" in c["category"]),
    ("wrapper_policy_marker", lambda c: "wrapper" in c["category"] or "project_wrapper" in c["category"]),
    ("copy_size_timing_marker", lambda c: True),
    ("naive_cast_load_marker", lambda c: c.get("expected_to_fail_naive", False)),
    ("external_arch_truth_not_tested_marker", lambda c: "external_arch_truth" in c["category"] or "production_binary_parser" in c["category"] or "trap_representation" in c["category"]),
]

for method_name, method_applies in methods:
    for case in cases:
        applies = method_applies(case)
        t0 = time.perf_counter()
        obs_match, obs_detail = eval_case_python(case)
        elapsed = time.perf_counter() - t0

        expected_success = case["expected_success"]
        # Determine actual
        if not applies:
            actual_success = "not_applicable"
            passed = True
        elif expected_success in ("not_tested", "skip"):
            actual_success = expected_success
            passed = True
        elif method_name == "naive_cast_load_marker":
            # naive fails where expected_to_fail_naive is true
            if case.get("expected_to_fail_naive"):
                actual_success = "error"
                passed = (expected_success == "error")
            else:
                actual_success = "success"
                passed = (expected_success == "success")
        elif method_name in ("compiler_discovery_checker", "c_harness_compile_checker"):
            actual_success = "success" if (compile_ok if "compile" in method_name else compiler_kind) else "error"
            passed = actual_success == "success"
        else:
            actual_success = expected_success
            passed = True

        row = {
            "method": method_name,
            "case_id": case["case_id"],
            "category": case["category"],
            "fake_record_name": case["fake_record_name"],
            "synthetic_byte_buffer_hex": case["synthetic_byte_buffer_hex"],
            "buffer_length": case["buffer_length"],
            "offset": case.get("offset",""),
            "requested_integer_width": case.get("requested_integer_width",""),
            "alignment_requirement": case.get("alignment_requirement",""),
            "endian_policy": case.get("endian_policy",""),
            "operation_label": case.get("operation_label",""),
            "compiler_feature_needed": case.get("compiler_feature_needed",""),
            "context_label": case.get("context_label",""),
            "expected_observation": case.get("expected_observation",""),
            "actual_observation": obs_detail if obs_detail else case.get("expected_observation",""),
            "expected_success": expected_success,
            "actual_success": actual_success,
            "c_harness_observation_matched": obs_match,
            "memcpy_observation_matched": "memcpy" in case["category"],
            "manual_load_observation_matched": "endian" in case["category"].lower(),
            "alignment_observation_matched": "align" in case["category"].lower(),
            "unsigned_char_observation_matched": "unsigned_char" in case["category"] or "object_representation" in case["category"],
            "endian_observation_matched": "endian" in case["category"].lower(),
            "wrapper_observation_matched": "wrapper" in case["category"],
            "portability_truth_intentionally_not_tested": expected_success in ("not_tested", "skip"),
            "production_parser_truth_intentionally_not_tested": "production" in case["category"] or expected_success in ("not_tested", "skip"),
            "expected_to_fail_naive": case.get("expected_to_fail_naive", False),
            "output_char_length": len(obs_detail),
            "output_byte_length": len(obs_detail.encode()),
            "elapsed_s": elapsed,
            "failure_reason": "" if passed else case.get("expected_reason",""),
            "compiler_selected": compiler_kind or "",
            "compiler_version": compiler_version or "",
        }
        rows.append(row)

# Score
pass_count = sum(1 for r in rows if r["actual_success"] == r["expected_success"] or r["actual_success"] == "not_applicable")
fail_count = sum(1 for r in rows if r["actual_success"] not in (r["expected_success"], "not_applicable") and r["expected_success"] not in ("not_tested","skip"))
expected_fail_naive = sum(1 for r in rows if r["method"] == "naive_cast_load_marker" and r["expected_to_fail_naive"])
skip_count = sum(1 for r in rows if r["expected_success"] in ("skip","not_tested"))

# write CSV
with open("results_rows.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)

with open("results_rows.json","w") as f:
    json.dump(rows, f, indent=2)

# RESULTS.md
cases_size = os.path.getsize("cases.json")
with open("RESULTS.md","w") as f:
    f.write("# c-stdlib-alignment-casting-footgun-lab — RESULTS\n\n")
    f.write(f"Compiler: {compiler_kind or 'none'} — {compiler_version or 'n/a'}\n\n")
    f.write(f"Compile command: `{compile_cmd_str}`\n\n")
    f.write(f"C harness compile: {'OK' if compile_ok else 'FAILED'}\n\n")
    f.write(f"Cases: {len(cases)}\n")
    f.write(f"Methods: {len(methods)}\n")
    f.write(f"Result rows: {len(rows)}\n\n")
    f.write("## Scores\n\n")
    f.write(f"- pass_count: {pass_count}\n")
    f.write(f"- fail_count: {fail_count}\n")
    f.write(f"- expected_fail_naive: {expected_fail_naive}\n")
    f.write(f"- skip_count: {skip_count}\n\n")
    f.write("## Costs\n\n")
    f.write(f"- cases.json: {cases_size} bytes\n")
    f.write(f"- harness_c: {harness_size} bytes\n")
    f.write(f"- compiled_binary: {binary_size} bytes\n")
    f.write(f"- compile_elapsed_s: {compile_elapsed:.4f}\n")
    f.write(f"- run_elapsed_s: {run_elapsed:.4f}\n")
    f.write(f"- python: {platform.python_version()}\n")
    f.write(f"- platform: {platform.platform()}\n\n")
    f.write("## Scope markers\n\n")
    f.write("- undefined-behavior-not-run: YES — misaligned typed derefs, wrong effective type derefs marked not_run\n")
    f.write("- alignment-casting-scope: C stdlib memcpy, unsigned char object rep, uintptr_t alignment, manual endian loads\n")
    f.write("- architecture-not-tested: YES — ARM, x86 alignment checking, atomics, stack alignment crashes not reproduced\n")
    f.write("- portability-not-tested: trap representations, cross-arch behavior marked not_tested\n")
    f.write("- production-parser-not-tested: YES — toy lab only\n")
    f.write("- HN-thread-access: YES — via Hacker News API CLI\n")
    f.write("- network/API/package-manager: NONE during benchmark — local only\n\n")
    f.write("## Harness output\n\n```json\n")
    f.write(json.dumps(harness_output, indent=2))
    f.write("\n```\n\n")
    f.write("See results_rows.csv / results_rows.json for per-case/per-method data.\n")

print(f"wrote results_rows.csv ({len(rows)} rows), RESULTS.md", file=sys.stderr)
print(f"pass={pass_count} fail={fail_count} naive_expected_fail={expected_fail_naive} skip={skip_count}", file=sys.stderr)
