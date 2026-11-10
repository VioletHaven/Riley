# Challenge 01 — Riley's first permission decision

**Difficulty:** Beginner. **Status:** Completed (questions 1–2). Optional extension not yet attempted.

You are designing a *practice-only* permission decision. No live Riley files should be changed.

```python
def decide(permission):
    if permission == "allow":
        return "allowed"
    elif permission == "ask":
        return "needs_approval"
    else:
        return "denied"
```

## Your challenge
1. Predict the result of `decide("ask")`.
2. Predict the result of `decide("mystery")`.
3. Optional: add a new explicit `"blocked"` branch that returns `"denied"`.

## What to learn
`if`, `elif`, `else`, function arguments, return values, and why unknown permissions are denied.

Completed answers: `decide("ask")` returns `"needs_approval"`; `decide("mystery")` returns `"denied"` because the `else` branch handles unknown values. A decision result does not itself perform an action. Optional extension remains available. You do not need to install anything to attempt this.
