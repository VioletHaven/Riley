# Lesson 01 — Decisions with Python

## Why this matters to Riley
Before Riley opens or changes a file, her permission gateway must decide whether the requested action is allowed, needs approval, or is denied.

## Example (practice only)
```python
def decide(permission):
    if permission == "allow":
        return "allowed"
    elif permission == "ask":
        return "needs_approval"
    else:
        return "denied"
```

`def` starts a function. `permission` is its argument. `if` checks a condition; `elif` checks another; `else` handles everything else. `return` gives back a result.

## Security lesson
Unknown permissions must be denied, not assumed safe. This simple example is *not* Riley's real authorization code.

## Try it
See [Challenge 01](challenges/challenge-01.md). No need to modify Riley's running code.
