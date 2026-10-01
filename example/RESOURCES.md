# C++ Memory Resources

## Knowledge

- [cppreference: new and delete](https://en.cppreference.com/w/cpp/language/new)
  The authoritative wording on allocation, matching delete, and what each
  expression returns. Use for: settling exactly what an expression does.
- [cppreference: delete](https://en.cppreference.com/w/cpp/language/delete)
  Covers destruction order, delete[], and placement delete. Use for: when the
  destructor runs relative to the free.
- [LearnCpp: pointers and memory](https://www.learncpp.com/cpp-tutorial/pointers-and-memory/)
  Long-running, example-first walkthrough with diagrams. Use for: the intro and
  memory-layout picture when a lesson needs more depth.
- [Clang AddressSanitizer docs](https://clang.llvm.org/docs/AddressSanitizer.html)
  How to build and read a sanitizer report. Use for: turning a lesson into a
  runnable check.
- [C++ Core Guidelines: R.11 "avoid calling new and delete explicitly"](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#R11-avoid-calling-new-and-delete-explicitly)
  The standard's own position on raw new. Use for: when to introduce
  `std::unique_ptr` instead of finishing the raw-pointer lesson.

## Wisdom (Communities)

- [r/cpp](https://reddit.com/r/cpp)
  Active, moderated. Use for: review requests on ownership patterns.
- [cppreference.com "Community" links per page](https://en.cppreference.com/w/)
  Each page links its own Stack Overflow tag and reference material.

## Gaps

- No good short reference found yet for allocator internals. Out of scope for
  now; revisit if the mission shifts toward allocation performance.