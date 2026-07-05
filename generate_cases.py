#!/usr/bin/env python3
"""Generate deterministic fake alignment/casting test cases for C stdlib footgun lab."""
import json
import random

random.seed(42)

# Fake names pool
fake_names = [
    "fake_bytes", "demo_buffer", "synthetic_word", "toy_packet",
    "example_block", "sample_blob", "fake_record", "demo_payload",
    "synthetic_offset", "toy_alignment_case", "fictional_header",
    "fake_u64_field", "sample_lane", "demo_chunk", "synthetic_alias_case",
    "toy_endian_case",
]

def hex_escape(b: bytes) -> str:
    return "".join(f"\\x{byte:02x}" for byte in b)

cases = []
cid = 1

def add_case(category, fake_name, buf_bytes, **fields):
    global cid
    case = {
        "case_id": f"c{cid:03d}",
        "category": category,
        "fake_record_name": fake_name,
        "synthetic_byte_buffer_hex": hex_escape(buf_bytes),
        "buffer_length": len(buf_bytes),
    }
    case.update(fields)
    cases.append(case)
    cid += 1

# --- unsigned char object representation (1 case, was 2) ---
buf = bytes([0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xde, 0xf0])
add_case(
    "unsigned_char_can_view_uint64_bytes",
    "demo_buffer",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="unsigned_char_view",
    compiler_feature_needed="none",
    context_label="object_representation_policy",
    expected_observation="unsigned_char_can_inspect_object_bytes",
    expected_success="success",
    expected_reason="char_view_directional_safe",
    expected_to_fail_naive=False,
)

# uint8_t aliasing portability marker
buf = bytes(range(8))
add_case(
    "uint8_t_aliasing_portability_marker",
    "synthetic_alias_case",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=1,
    endian_policy="native",
    operation_label="uint8_t_aliasing_check",
    compiler_feature_needed="stdint_h",
    context_label="strict_aliasing_caveat",
    expected_observation="uint8_t_is_typically_unsigned_char_alias_safe_direction_matters",
    expected_success="success",
    expected_reason="uint8_t_typically_char_type",
    expected_to_fail_naive=False,
)

# char_view_directionality
buf = bytes([0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff, 0x11, 0x22])
add_case(
    "char_view_directionality_marker",
    "demo_buffer",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="char_view_directionality",
    compiler_feature_needed="none",
    context_label="object_representation_policy",
    expected_observation="char_can_view_object_but_reverse_not_automatically_safe",
    expected_success="success",
    expected_reason="unsigned_char_object_representation_is_directional",
    expected_to_fail_naive=True,
)

# pointer_cast_without_deref
buf = bytes([0x01]*8)
add_case(
    "pointer_cast_without_deref_marker",
    "fake_bytes",
    buf,
    offset=1,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="cast_without_deref",
    compiler_feature_needed="none",
    context_label="alignment_policy",
    expected_observation="cast_alone_not_same_as_deref",
    expected_success="success",
    expected_reason="cast_without_deref_is_not_UB_by_itself",
    expected_to_fail_naive=False,
)

# misaligned_uint64_deref_not_run (1 case, was 3)
buf = bytes(range(16))
add_case(
    "misaligned_uint64_deref_not_run",
    "toy_alignment_case",
    buf,
    offset=1,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="unsafe_deref_misaligned",
    compiler_feature_needed="none",
    context_label="alignment_policy",
    expected_observation="not_run_UB_misaligned_deref",
    expected_success="not_tested",
    expected_reason="misaligned_typed_deref_is_not_portable",
    expected_to_fail_naive=True,
)

# wrong_effective_type_deref_not_run
buf = bytes([0x11]*8)
add_case(
    "wrong_effective_type_deref_not_run",
    "synthetic_alias_case",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="unsafe_deref_effective_type",
    compiler_feature_needed="none",
    context_label="effective_type_caveat",
    expected_observation="not_run_UB_wrong_effective_type",
    expected_success="not_tested",
    expected_reason="dereferencing_through_wrong_effective_type_is_UB",
    expected_to_fail_naive=True,
)

# aligned_uint64_object_read_success (1 case, was 2)
buf = bytes([0xef, 0xbe, 0xad, 0xde, 0x00, 0x00, 0x00, 0x00] * 2)
add_case(
    "aligned_uint64_object_read_success",
    "fake_u64_field",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="aligned_object_read",
    compiler_feature_needed="none",
    context_label="alignment_policy",
    expected_observation="aligned_object_read_success",
    expected_success="success",
    expected_reason="properly_aligned_object_read_is_defined",
    expected_to_fail_naive=False,
)

# memcpy_load_u64_native_order (1 case, was 2)
buf = bytes([j & 0xff for j in range(8)])
add_case(
    "memcpy_load_u64_native_order",
    "demo_payload",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=1,
    endian_policy="native",
    operation_label="memcpy_load",
    compiler_feature_needed="string_h",
    context_label="memcpy_policy",
    expected_observation="memcpy_loads_bytes_into_integer_object_portably",
    expected_success="success",
    expected_reason="memcpy_is_portable_byte_copy",
    expected_to_fail_naive=False,
)

# memcpy_load_u32_native_order
buf = bytes([0x78, 0x56, 0x34, 0x12])
add_case(
    "memcpy_load_u32_native_order",
    "synthetic_word",
    buf,
    offset=0,
    requested_integer_width=32,
    alignment_requirement=1,
    endian_policy="native",
    operation_label="memcpy_load",
    compiler_feature_needed="string_h",
    context_label="memcpy_policy",
    expected_observation="memcpy_load_u32_native",
    expected_success="success",
    expected_reason="memcpy_portable",
    expected_to_fail_naive=False,
)

# memcpy_store_roundtrip_u64
buf = bytes(8)
add_case(
    "memcpy_store_roundtrip_u64",
    "sample_blob",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=1,
    endian_policy="native",
    operation_label="memcpy_roundtrip",
    compiler_feature_needed="string_h",
    context_label="memcpy_policy",
    expected_observation="memcpy_roundtrip_preserves_bits",
    expected_success="success",
    expected_reason="memcpy_roundtrip",
    expected_to_fail_naive=False,
)

# memmove_overlap_byte_buffer
buf = bytes(range(16))
add_case(
    "memmove_overlap_byte_buffer",
    "example_block",
    buf,
    offset=2,
    requested_integer_width=0,
    alignment_requirement=1,
    endian_policy="native",
    operation_label="memmove_overlap",
    compiler_feature_needed="string_h",
    context_label="memcpy_policy",
    expected_observation="memmove_handles_overlap_safely",
    expected_success="success",
    expected_reason="memmove_overlap_safe",
    expected_to_fail_naive=False,
)

# manual little endian loads
for width, name in [(16, "manual_little_endian_load_u16"), (32, "manual_little_endian_load_u32"), (64, "manual_little_endian_load_u64")]:
    nbytes = width // 8
    buf = bytes([j & 0xff for j in range(nbytes)])
    add_case(
        name,
        "toy_endian_case",
        buf,
        offset=0,
        requested_integer_width=width,
        alignment_requirement=1,
        endian_policy="little",
        operation_label="manual_byte_shift_load",
        compiler_feature_needed="none",
        context_label="endian_caveat",
        expected_observation=f"manual_le_load_u{width}_explicit_endian",
        expected_success="success",
        expected_reason="manual_byte_shift_explicit_endian",
        expected_to_fail_naive=False,
    )

# manual big endian loads
for width, name in [(16, "manual_big_endian_load_u16"), (32, "manual_big_endian_load_u32"), (64, "manual_big_endian_load_u64")]:
    nbytes = width // 8
    buf = bytes([j & 0xff for j in range(nbytes)])
    add_case(
        name,
        "toy_endian_case",
        buf,
        offset=0,
        requested_integer_width=width,
        alignment_requirement=1,
        endian_policy="big",
        operation_label="manual_byte_shift_load",
        compiler_feature_needed="none",
        context_label="endian_caveat",
        expected_observation=f"manual_be_load_u{width}_explicit_endian",
        expected_success="success",
        expected_reason="manual_byte_shift_explicit_endian",
        expected_to_fail_naive=False,
    )

# endian_policy_native_vs_explicit
buf = bytes([0x01, 0x02, 0x03, 0x04])
add_case(
    "endian_policy_native_vs_explicit",
    "toy_endian_case",
    buf,
    offset=0,
    requested_integer_width=32,
    alignment_requirement=1,
    endian_policy="native",
    operation_label="endian_policy_check",
    compiler_feature_needed="none",
    context_label="endian_caveat",
    expected_observation="native_endian_differs_from_explicit_wire_format",
    expected_success="success",
    expected_reason="endian_policy_matters",
    expected_to_fail_naive=True,
)

# memcpy_does_not_choose_endian
buf = bytes([0xaa, 0xbb, 0xcc, 0xdd])
add_case(
    "memcpy_does_not_choose_endian",
    "demo_chunk",
    buf,
    offset=0,
    requested_integer_width=32,
    alignment_requirement=1,
    endian_policy="native",
    operation_label="memcpy_load",
    compiler_feature_needed="string_h",
    context_label="endian_caveat",
    expected_observation="memcpy_copies_bytes_not_endian_converts",
    expected_success="success",
    expected_reason="memcpy_no_endian_conversion",
    expected_to_fail_naive=True,
)

# unaligned_offset_detected_by_uintptr (2 cases, was 4)
for off in [1, 3]:
    buf = bytes(range(16))
    add_case(
        "unaligned_offset_detected_by_uintptr",
        "toy_alignment_case",
        buf,
        offset=off,
        requested_integer_width=64,
        alignment_requirement=8,
        endian_policy="native",
        operation_label="alignment_check_uintptr",
        compiler_feature_needed="stdint_h",
        context_label="alignment_policy",
        expected_observation="unaligned_offset_detected",
        expected_success="success",
        expected_reason="uintptr_mod_align_check",
        expected_to_fail_naive=False,
    )

# aligned_offset_detected_by_uintptr (1 case, was 2)
buf = bytes(range(16))
add_case(
    "aligned_offset_detected_by_uintptr",
    "toy_alignment_case",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="alignment_check_uintptr",
    compiler_feature_needed="stdint_h",
    context_label="alignment_policy",
    expected_observation="aligned_offset_detected",
    expected_success="success",
    expected_reason="uintptr_mod_align_check",
    expected_to_fail_naive=False,
)

# _Alignof markers
for width, typ in [(16, "uint16"), (32, "uint32"), (64, "uint64")]:
    buf = bytes([0]*(width//8))
    add_case(
        f"_Alignof_uint{width}_marker",
        "fictional_header",
        buf,
        offset=0,
        requested_integer_width=width,
        alignment_requirement=width//8,
        endian_policy="native",
        operation_label="alignof_query",
        compiler_feature_needed="stdalign_h",
        context_label="alignment_policy",
        expected_observation=f"alignof_uint{width}_observed",
        expected_success="success",
        expected_reason="alignof_marker",
        expected_to_fail_naive=False,
    )

# malloc_alignment_observation_marker
buf = bytes(8)
add_case(
    "malloc_alignment_observation_marker",
    "fake_record",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="malloc_align_check",
    compiler_feature_needed="stdlib_h",
    context_label="alignment_policy",
    expected_observation="malloc_returns_suitably_aligned_storage",
    expected_success="success",
    expected_reason="malloc_alignment_guarantee",
    expected_to_fail_naive=False,
)

# stack_object_alignment_observation_marker
buf = bytes(8)
add_case(
    "stack_object_alignment_observation_marker",
    "sample_lane",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="stack_align_check",
    compiler_feature_needed="none",
    context_label="alignment_policy",
    expected_observation="stack_object_naturally_aligned",
    expected_success="success",
    expected_reason="stack_alignment",
    expected_to_fail_naive=False,
)

# struct_padding_marker
buf = bytes(16)
add_case(
    "struct_padding_marker",
    "fake_record",
    buf,
    offset=0,
    requested_integer_width=0,
    alignment_requirement=1,
    endian_policy="native",
    operation_label="struct_sizeof_offsetof",
    compiler_feature_needed="stddef_h",
    context_label="alignment_policy",
    expected_observation="struct_may_contain_padding",
    expected_success="success",
    expected_reason="struct_padding_exists",
    expected_to_fail_naive=False,
)

# offsetof_padding_marker
buf = bytes(16)
add_case(
    "offsetof_padding_marker",
    "fake_record",
    buf,
    offset=0,
    requested_integer_width=0,
    alignment_requirement=1,
    endian_policy="native",
    operation_label="offsetof_check",
    compiler_feature_needed="stddef_h",
    context_label="alignment_policy",
    expected_observation="offsetof_reveals_padding",
    expected_success="success",
    expected_reason="offsetof_marker",
    expected_to_fail_naive=False,
)

# packed_struct_extension_not_required
buf = bytes(8)
add_case(
    "packed_struct_extension_not_required",
    "toy_packet",
    buf,
    offset=1,
    requested_integer_width=32,
    alignment_requirement=1,
    endian_policy="native",
    operation_label="packed_struct_context",
    compiler_feature_needed="gcc_extension",
    context_label="compiler_extension_not_required",
    expected_observation="packed_struct_not_required_in_lab",
    expected_success="skip",
    expected_reason="packed_struct_is_compiler_extension_not_ISO_C",
    expected_to_fail_naive=False,
)

# union_type_punning_context_not_run
buf = bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88])
add_case(
    "union_type_punning_context_not_run",
    "synthetic_alias_case",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="union_punning_context",
    compiler_feature_needed="none",
    context_label="strict_aliasing_caveat",
    expected_observation="union_punning_discussed_in_HN_not_run_as_proof",
    expected_success="not_tested",
    expected_reason="union_punning_portability_caveats_C_vs_Cpp",
    expected_to_fail_naive=False,
)

# padding_bytes_not_interpreted_marker
buf = bytes(16)
add_case(
    "padding_bytes_not_interpreted_marker",
    "fake_record",
    buf,
    offset=0,
    requested_integer_width=0,
    alignment_requirement=1,
    endian_policy="native",
    operation_label="padding_bytes",
    compiler_feature_needed="none",
    context_label="object_representation_policy",
    expected_observation="padding_bytes_not_meaningful",
    expected_success="success",
    expected_reason="padding_bytes_undefined",
    expected_to_fail_naive=False,
)

# object_representation_bytes_marker
buf = bytes([0xde, 0xad, 0xbe, 0xef, 0xca, 0xfe, 0xba, 0xbe])
add_case(
    "object_representation_bytes_marker",
    "demo_buffer",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="object_rep_view",
    compiler_feature_needed="none",
    context_label="object_representation_policy",
    expected_observation="object_representation_inspectable_via_unsigned_char",
    expected_success="success",
    expected_reason="unsigned_char_object_rep",
    expected_to_fail_naive=False,
)

# effective_type_context_marker
buf = bytes(8)
add_case(
    "effective_type_context_marker",
    "synthetic_alias_case",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="effective_type_context",
    compiler_feature_needed="none",
    context_label="effective_type_caveat",
    expected_observation="effective_type_determines_aliasing_legality",
    expected_success="success",
    expected_reason="effective_type_marker",
    expected_to_fail_naive=False,
)

# strict_aliasing_context_marker
buf = bytes(8)
add_case(
    "strict_aliasing_context_marker",
    "synthetic_alias_case",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="strict_aliasing_context",
    compiler_feature_needed="none",
    context_label="strict_aliasing_caveat",
    expected_observation="strict_aliasing_rules_restrict_type_punning",
    expected_success="success",
    expected_reason="strict_aliasing_marker",
    expected_to_fail_naive=True,
)

# cast_align_warning_context_marker
buf = bytes(8)
add_case(
    "cast_align_warning_context_marker",
    "demo_chunk",
    buf,
    offset=1,
    requested_integer_width=32,
    alignment_requirement=4,
    endian_policy="native",
    operation_label="cast_align_warning",
    compiler_feature_needed="gcc_Wcast_align",
    context_label="diagnostic_not_required",
    expected_observation="Wcast_align_would_warn_but_not_proof",
    expected_success="success",
    expected_reason="diagnostic_marker",
    expected_to_fail_naive=False,
)

# x86_unaligned_success_not_proved
buf = bytes(range(16))
add_case(
    "x86_unaligned_success_not_proved",
    "toy_alignment_case",
    buf,
    offset=1,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="arch_context",
    compiler_feature_needed="none",
    context_label="architecture_not_tested",
    expected_observation="x86_permissive_behavior_does_not_prove_portability",
    expected_success="not_tested",
    expected_reason="x86_behavior_not_proof",
    expected_to_fail_naive=True,
)

# ARM_alignment_fault_not_reproduced
buf = bytes(range(16))
add_case(
    "ARM_alignment_fault_not_reproduced",
    "toy_alignment_case",
    buf,
    offset=1,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="arch_context",
    compiler_feature_needed="none",
    context_label="architecture_not_tested",
    expected_observation="ARM_fault_not_reproduced_locally",
    expected_success="not_tested",
    expected_reason="ARM_not_tested",
    expected_to_fail_naive=False,
)

# compiler_optimization_not_proof
buf = bytes(8)
add_case(
    "compiler_optimization_not_proof",
    "demo_payload",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="opt_context",
    compiler_feature_needed="none",
    context_label="diagnostic_not_required",
    expected_observation="compiler_optimizing_memcpy_does_not_prove_UB_safe",
    expected_success="success",
    expected_reason="optimization_not_proof",
    expected_to_fail_naive=False,
)

# memcpy_optimization_not_required
buf = bytes(8)
add_case(
    "memcpy_optimization_not_required",
    "demo_payload",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=1,
    endian_policy="native",
    operation_label="memcpy_opt_context",
    compiler_feature_needed="none",
    context_label="diagnostic_not_required",
    expected_observation="memcpy_may_optimize_but_not_required",
    expected_success="success",
    expected_reason="memcpy_opt_marker",
    expected_to_fail_naive=False,
)

# project wrapper load_result struct marker
buf = bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88])
add_case(
    "project_wrapper_load_result_struct_marker",
    "demo_payload",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="little",
    operation_label="wrapper_load",
    compiler_feature_needed="none",
    context_label="memcpy_policy",
    expected_observation="wrapper_records_status_width_offset_aligned_endian_value",
    expected_success="success",
    expected_reason="wrapper_marker",
    expected_to_fail_naive=False,
)

# wrapper records aligned flag
buf = bytes(range(16))
add_case(
    "wrapper_records_aligned_flag_marker",
    "toy_alignment_case",
    buf,
    offset=2,
    requested_integer_width=32,
    alignment_requirement=4,
    endian_policy="native",
    operation_label="wrapper_load",
    compiler_feature_needed="none",
    context_label="alignment_policy",
    expected_observation="wrapper_records_aligned_false_for_misaligned_offset",
    expected_success="success",
    expected_reason="wrapper_aligned_flag",
    expected_to_fail_naive=False,
)

# wrapper records endian policy
buf = bytes([0x01, 0x02, 0x03, 0x04])
add_case(
    "wrapper_records_endian_policy_marker",
    "toy_endian_case",
    buf,
    offset=0,
    requested_integer_width=32,
    alignment_requirement=1,
    endian_policy="big",
    operation_label="wrapper_load",
    compiler_feature_needed="none",
    context_label="endian_caveat",
    expected_observation="wrapper_records_endian_policy_explicitly",
    expected_success="success",
    expected_reason="wrapper_endian_marker",
    expected_to_fail_naive=False,
)

# wrapper rejects unsafe_deref policy
buf = bytes([0xff]*8)
add_case(
    "wrapper_rejects_unsafe_deref_policy_marker",
    "demo_payload",
    buf,
    offset=1,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="wrapper_load",
    compiler_feature_needed="none",
    context_label="alignment_policy",
    expected_observation="wrapper_rejects_unsafe_deref",
    expected_success="success",
    expected_reason="wrapper_safety_policy",
    expected_to_fail_naive=True,
)

# naive_cast_load_marker expected to fail
buf = bytes(range(8))
add_case(
    "naive_cast_load_marker",
    "fake_bytes",
    buf,
    offset=1,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="naive_cast_deref",
    compiler_feature_needed="none",
    context_label="naive_cast",
    expected_observation="naive_cast_assumes_any_byte_ptr_is_typed_ptr",
    expected_success="error",
    expected_reason="naive_cast_ignores_alignment_and_effective_type",
    expected_to_fail_naive=True,
)

# naive_native_endian_marker expected to fail
buf = bytes([0x01, 0x00, 0x00, 0x00])
add_case(
    "naive_native_endian_marker",
    "toy_endian_case",
    buf,
    offset=0,
    requested_integer_width=32,
    alignment_requirement=1,
    endian_policy="big",
    operation_label="naive_endian",
    compiler_feature_needed="none",
    context_label="endian_caveat",
    expected_observation="naive_assumes_native_endian_is_wire_format",
    expected_success="error",
    expected_reason="naive_endian_footgun",
    expected_to_fail_naive=True,
)

# safety_caveat
buf = bytes(8)
add_case(
    "safety_caveat_marker",
    "fake_bytes",
    buf,
    offset=0,
    requested_integer_width=64,
    alignment_requirement=8,
    endian_policy="native",
    operation_label="safety_caveat",
    compiler_feature_needed="none",
    context_label="portability_not_tested",
    expected_observation="toy_lab_not_production_parser",
    expected_success="success",
    expected_reason="safety_scope",
    expected_to_fail_naive=False,
)

with open("cases.json", "w") as f:
    json.dump(cases, f, indent=2)

print(f"wrote {len(cases)} cases to cases.json")
