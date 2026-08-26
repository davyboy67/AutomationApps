### 1. Think before coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity first

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the user's request.

### 4. Comments earn their place

**Explain why, never what. The code says what it does.**

Assume a competent developer is reading. They can follow the code; what they cannot recover is
the reasoning that is no longer on the page.

- Never restate what the code does. If a comment paraphrases the line below it, delete it.
- Only write a comment when a competent developer would ask "why is this here?" and not be able
  to answer it from the code, the types, or the test names.
- Good reasons to comment: a non-obvious constraint, a decision that looks wrong but is not, a
  behaviour inherited from somewhere the reader cannot see, an ordering that matters.
- Prefer making the code explain itself — a better name, a smaller function, a named constant —
  over adding a comment.
- Delete comments that have gone stale rather than updating them into vagueness.

Before keeping a comment, ask: "would a competent developer be confused without this?" If no,
delete it.

### 5. Goal-driven execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---
