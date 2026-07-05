# HN Thread Evidence

**Thread:** Unaligned accesses in C/C++: what, why and solutions to do it properly  
**HN URL:** https://news.ycombinator.com/item?id=38472174  
**Linked article:** https://blog.quarkslab.com/unaligned-accesses-in-cc-what-why-and-solutions-to-do-it-properly.html  
**Accessed via:** Hacker News API CLI (`python3 ./hackernews get-item --id 38472174`)  
**Date accessed:** 2026-07-05  
**Comment count:** 54 descendants

## Key commenters and sentiments

### JonChesterfield (38473755)
- "I expected this to be an aliasing violation and was not disappointed. Dereferencing a uint8_t through a uint64_t is undefined behaviour whatever the target architecture is."
- "That it works for the author on x64 just means the compiler didn't break it this time around."
- "an 8 byte aligned uint8_t also can't be dereferenced via a uint64_t. It isn't UB because the alignment is wrong, it's UB by definition and also the alignment might be wrong."
- "This is a woeful state of affairs propagated by an ill founded and widespread confidence that the C and C++ standards probably aren't as hostile to type aliasing as they actually are."

### gpderetta (38473820, reply)
- "If uint8_t is a char type (and invariably it is), then it is fully defined."
- "Similarly, it is perfectly safe to cast a correctly aligned uint8_t* to uint64_t* and dereference it as long as you originally stored an uint64_t into it (or the compiler can't prove you didn't)."
- "Remember aliasing UB is always on derefencing with the wrong dynamic type, not on casting pointers."

### pkkm (38474417)
- "while I get the historical reasons for strict aliasing, I wish it hadn't been created. Just make -fno-strict-aliasing the default and normalize the abundant use of restrict"

### AnimalMuppet (38473899)
- "if you're playing this kind of game, the compiler cannot type-check what you're doing (or sanity-check it in any other way). You're outside the area covered by the standard. You're coding without a net."
- "But C and C++ are explicitly intended for this kind of situation."

### derf_ (38473966)
- SIMD intrinsics alignment footgun: `_mm_cvtepi8_epi32()` / PMOVSXBD – intrinsic takes `__m128i` (16-byte aligned) but instruction with memory operand imposes no alignment restriction
- "Tools like UBSan will also (correctly) complain about it."
- Workarounds from the article combined with `_mm_cvtsi32_si128()` are the only reliable solution found

### mlochbaum (38474448)
- Linux kernel packed struct `unaligned()` macro solution
- "`#define unaligned(P) (((struct { typeof(*(P)) x; } __attribute__((packed))*)(P))->x)`"

### JonChesterfield (38476409, reply)
- "Uses of pointers to members of packed structs are prone to being miscompiled by GCC"

### el_pollo_diablo (38476270)
- Union type punning solution for unaligned 64-bit load
- "Type punning through a union is explicitly supported by the C standard"
- "GCC appears to compile this function to a plain unaligned load at optimization level 2, when supported, e.g. on arm64"
- Follow-up: compiler can still understand and aggressively optimize in freestanding environment (advantage over memcpy)

### amluto (38474076)
- "The 'multiple loads' solution is IMO correct. It does precisely what it looks like it does, it doesn't rely on any assumptions about how integers are represented, and, IMO best of all, it completely gets rid of the 'native endian' crap that has plagued C programs for decades."

### wyldfire (38474243)
- "`-fsanitize=undefined` helps uncover this kind of UB and more. While you're there, pile on with ASan: `-fsanitize=address,undefined`."

### tralarpa (38473891)
- "With gcc, the option `-Wcast-align=strict` is useful."
- "if the buffer to convert is very large, one could first check the alignment of the pointer (with alignof(T)) in C++"

### 12345ieee (38475043)
- "As other comments say, this is missing packed unions, which is the best solution I've found while writing a memory editor."

### dataflow (38474926)
- "Q: How do you do atomic unaligned accesses from C++?"

### cesarb / JonChesterfield / cjensen (replies to atomic question)
- Generally not possible portably; x86 allows it but locks the whole bus
- "C++ cannot represent an atomic type with less than natural alignment"
- "Portably? You don't. That's a CPU limitation"

### knorker (38474684)
- "The right way to cast stuff in memory since C++20 is std::bit_cast, right?"

### Ono-Sendai (38474101)
- "memcpy was quite slow in my tests however, it was ~twice as fast to check the alignment and load as floats"

### pengaru (38475582, reply)
- "There have been several memcpy performance regressions affecting modern CPUs in recent years"

### epx (38475034)
- "Had a problem like that while porting an IEEE 11073 parser library to Emscripten. Funnily enough, the code worked happily in x86 and ARM environments, but failed in Emscripten."

### rwmj (38475591)
- Stack alignment crash: calling from assembly back to C without honoring 16-byte stack alignment, compiler-generated vector access crashed – "The stack was only unaligned some of the time and the crash happened very distant from the wrapper"

### xscott (38476929)
- "I think we're getting to the point where C++ users should define two classes: Integer { // uses unsigned integers … }; Pointer { // uses void* and memcpy for all loads or stores }; … Then we can safely ignore all the undefined behavior which has been so eagerly embraced by the compiler writers"

## Themes summary

The thread is NOT just about unaligned loads. Major recurring themes:

1. Strict aliasing / effective type violations (not just alignment)
2. Cast vs dereference distinction
3. uint8_t / unsigned char aliasing rules, directionality of object-representation access
4. memcpy as portable byte-copy
5. Manual byte-shift loads, endian policy
6. x86 permissive behavior ≠ portable C
7. Packed structs / unions – discussed but with caveats (GCC miscompilation, C vs C++ rules)
8. -fno-strict-aliasing, restrict
9. Sanitizers, -Wcast-align as diagnostics not proof
10. C vs C++ rules (bit_cast, union punning)
11. Compiler optimizations / TBAA
12. SIMD intrinsics alignment footguns
13. Stack alignment crashes
14. Atomic unaligned accesses (generally not portable)
15. "Coding without a net"
16. Emscripten / cross-platform surprises
17. memcpy performance concerns / regressions

## Raw API output

Full JSON responses from the Hacker News API are available in the tool invocation logs for this session. Top-level story ID 38472174, 15 direct children, 54 total descendants. Key comment IDs: 38473755, 38473820, 38474417, 38473899, 38473966, 38474448, 38476409, 38476270, 38474076, 38474243, 38473891, 38475043, 38474926, 38474684, 38474101, 38475034, 38475591, 38475582, 38476929.
