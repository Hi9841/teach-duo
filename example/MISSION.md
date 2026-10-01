# Mission: C++ memory, confidently

## Why

Ship C++ that does not leak or corrupt memory under load. Reading code and
spotting a missing `delete` or a dangling pointer has to be automatic, not
something I have to reason about carefully every time.

## Success looks like

- Point at any `new` and say who deletes it, or admit nobody does.
- Read a `delete` and know whether the pointer is now dangling.
- Choose correctly between a stack value and a heap allocation without thinking.
- Explain to a colleague what `p` and `*p` each hold.

## Constraints

- I already know basic C++ syntax, classes, and templates.
- Short lessons during the workday, not weekend marathons.
- Sanitizers matter more than theory: I want to run the code too.

## Out of scope

- Allocator internals and custom `operator new`.
- Multithreading and lock-free structures.
- Performance tuning of allocation-heavy code.