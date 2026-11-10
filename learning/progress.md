# Learning progress

## Started
- 2026-11-10: Agreed to learn as we build with optional coding challenges and running notes.
- Lesson 01 introduced: conditional decisions and deny-by-default.
- Challenge 01 completed in chat: correctly identified `decide("ask")` as `"needs_approval"` and unknown `"mystery"` as `"denied"` via `else`. Clarified that a returned decision is not itself an approval prompt or executed action.

## Future topics
Functions and modules; permission scopes; filesystem safety; unit testing; audit logs; proactive suggestions.

Update this log only after discussing completed lessons or challenges. Do not mark a challenge complete without the learner's attempt.

- Bonus challenge completed: correctly predicted `permission = "blocked"` prints `Denied` through the `else` branch. Lesson 01 marked complete.

- Lesson 02 challenge completed: correctly explained how `greet(name)` receives an argument, returns a greeting, stores it in `message`, and prints the result. Clarified that string arguments require quotes (e.g., `greet("Jack")`).

- Lesson 02 follow-up: correctly identified `check_permission("delete")` returns `"needs_approval"`. Proposed permission learning: Riley should ask about unfamiliar requests and remember user-approved scopes to avoid repeated prompts. Design distinction: unknown operations remain denied by the executor; Riley may separately request narrowly scoped permission for supported capabilities, with explicit user approval, expiration, and revocation.
