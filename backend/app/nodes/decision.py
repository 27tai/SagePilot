"""
Decision node (conditional branch).

Evaluates a condition against the incoming payload and injects a `_branch`
key ("true" | "false") into the output. The workflow executor reads this key,
routes execution down the matching branch, and strips the key before passing
the payload to the next node.

Config keys:
  field    (str): the payload key to evaluate
  operator (str): comparison operator (see OPERATORS)
  value    (any): the comparison value (unused for is_empty)

Supported operators:
  equals, not_equals, greater_than, less_than, contains, is_empty
"""

from __future__ import annotations

from typing import Any, Callable

from .base import BaseNode, NodeExecutionError

OperatorFn = Callable[[Any, Any], bool]

OPERATORS: dict[str, OperatorFn] = {
    "equals":        lambda a, b: str(a) == str(b),
    "not_equals":    lambda a, b: str(a) != str(b),
    "greater_than":  lambda a, b: float(a) > float(b),
    "less_than":     lambda a, b: float(a) < float(b),
    "contains":      lambda a, b: str(b).lower() in str(a).lower(),
    "is_empty":      lambda a, b: a is None or str(a).strip() == "",
}


class DecisionNode(BaseNode):
    node_type = "decision"

    def validate_config(self) -> None:
        if not self.config.get("field"):
            raise ValueError("DecisionNode: 'field' is required.")
        operator = self.config.get("operator", "")
        if operator not in OPERATORS:
            raise ValueError(
                f"DecisionNode: unknown operator '{operator}'. "
                f"Supported: {list(OPERATORS)}"
            )

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.validate_config()

        field: str = self.config["field"]
        operator: str = self.config["operator"]
        compare_value: Any = self.config.get("value", "")

        if field not in payload:
            raise NodeExecutionError(
                f"DecisionNode: field '{field}' not found in payload. "
                f"Available: {list(payload.keys())}"
            )

        try:
            result = OPERATORS[operator](payload[field], compare_value)
        except (ValueError, TypeError) as exc:
            raise NodeExecutionError(
                f"DecisionNode: could not compare '{field}' with '{compare_value}' "
                f"using operator '{operator}': {exc}"
            )

        branch = "true" if result else "false"

        # _branch is a signal for the workflow executor — stripped before
        # the payload reaches the next node.
        return {**payload, "_branch": branch}
