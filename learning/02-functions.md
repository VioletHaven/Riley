# Lesson 02 — Functions and return values

A **function** is a reusable named piece of code. Riley's permission module uses `decide(action, target=..., workspace=...)` to return a decision without performing an action.

```python
def greet(name):
    return "Hello, " + name

message = greet("Riley")
print(message)
```

- `def` defines the function.
- `name` is a parameter.
- `"Riley"` is the argument supplied when calling it.
- `return` hands a value back to the caller.
- `print` displays a value.

## In Riley's actual code
`riley/permissions.py` defines `decide(...)`, returning a `PermissionResult` containing `decision` and `reason`. The function does not open files or ask the user by itself.

## Challenge
Predict the output of `print(greet("Riley"))`. Then explain what happens if we call `greet("Keylan")` instead.

Optional stretch: Why is returning a decision safer than letting the function directly execute a file operation?
