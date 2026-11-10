# Lesson 03 — Remembering permissions safely

Riley's first permission-learning building block is `riley/grants.py`. It stores **temporary, exact-file grants in memory**. It does not yet display an approval prompt, write to disk, or connect to the running app.

## New ideas
- **Class:** A blueprint for objects. `GrantStore` manages a collection of grants.
- **Method:** A function belonging to a class, such as `store.revoke(...)`.
- **Expiration:** A grant stops working after a specified time.
- **Scope:** A grant for `a.txt` must not work for `b.txt`.
- **Deny by default:** An unknown action cannot be made safe by merely asking for a generic approval.

## Challenge 03
Imagine you approved Riley to **write** `notes.txt` for five minutes.

1. Can Riley use that grant to **delete** `notes.txt`?
2. Can she use it to **write** `secrets.txt`?
3. What happens after six minutes?

Answer in your own words. No code required.

## Design note
This is not the finished approval system. A real UI, authentication binding, persistence policy, audit records, and safe execution integration are still required. No model-supplied `user_approved=True` value should ever count as actual consent.
