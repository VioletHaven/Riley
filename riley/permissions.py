"""Pure, deny-by-default permission decisions for Riley.

This module makes decisions only; it never performs computer actions.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Decision = Literal["allow", "ask", "deny"]


@dataclass(frozen=True)
class PermissionResult:
    decision: Decision
    reason: str


# Explicit action names are part of the security boundary. New tools need
# deliberate policy review rather than inheriting permissive defaults.
POLICY = {
    "workspace.read": "allow",
    "workspace.write": "ask",
    "workspace.delete": "ask",
    "memory.preference.save": "allow",
    "memory.sensitive.save": "ask",
    "initiative.suggest": "allow",
    "computer.open_app": "ask",
    "computer.send_message": "ask",
}


def decide(action: str, *, target: str = "", workspace: str = "") -> PermissionResult:
    """Return an authorization recommendation, never an execution grant.

    File actions require a path inside the explicitly configured workspace.
    An 'allow' result is not a substitute for runtime checks and does not
    authorize actions by itself. A separate executor must enforce policy.
    """
    if not isinstance(action, str) or action not in POLICY:
        return PermissionResult("deny", "Unknown or unsupported action")
    if action.startswith("workspace."):
        if not isinstance(target, str) or not target or "\x00" in target:
            return PermissionResult("deny", "A valid file target is required")
        if not isinstance(workspace, str) or not workspace:
            return PermissionResult("deny", "No approved workspace configured")
        try:
            root = Path(workspace).resolve(strict=True)
            if not root.is_dir():
                return PermissionResult("deny", "Approved workspace is not a directory")
            candidate = Path(target)
            resolved = (root / candidate).resolve(strict=False)
            if resolved == root or not resolved.is_relative_to(root):
                return PermissionResult("deny", "Target is outside the approved workspace")
        except (OSError, ValueError, RuntimeError):
            return PermissionResult("deny", "Cannot validate workspace target")
    return PermissionResult(POLICY[action], "Explicit policy rule")
