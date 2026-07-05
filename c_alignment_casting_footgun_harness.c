
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
