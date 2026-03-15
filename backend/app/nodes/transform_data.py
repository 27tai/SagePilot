"""
Transform Data node.

Applies a deterministic transformation to the incoming payload.

Config keys:
  transformation (str): one of the supported transform types (see TRANSFORMS)
  field (str):          the key in the payload to operate on
  params (dict):        transformation-specific parameters

Supported transformations
  - uppercase:    converts field value to uppercase string
  - append_text:  appends params["text"] to the field value
  - prepend_text: prepends params["text"] to the field value
  - multiply:     multiplies field value by params["factor"] (numeric)
  - rename_key:   renames field to params["new_key"]

Adding a new transformation:
  Add a function with signature (value, params) -> new_value to TRANSFORMS dict.
"""

from __future__ import annotations

from typing import Any, Callable

from .base import BaseNode, NodeExecutionError

# ---------------------------------------------------------------------------
# Transform function registry
# Each function receives (current_value, params_dict) and returns new_value.
# ---------------------------------------------------------------------------

def _uppercase(value: Any, params: dict) -> str:
    return str(value).upper()


def _append_text(value: Any, params: dict) -> str:
    text = params.get("text", "")
    return str(value) + str(text)


def _prepend_text(value: Any, params: dict) -> str:
    text = params.get("text", "")
    return str(text) + str(value)


def _multiply(value: Any, params: dict) -> float:
    factor = params.get("factor", 1)
    return float(value) * float(factor)


def _rename_key(value: Any, params: dict) -> Any:
    # Handled specially below — returns the value unchanged;
    # the key rename logic lives in TransformDataNode.execute()
    return value


TRANSFORMS: dict[str, Callable[[Any, dict], Any]] = {
    "uppercase": _uppercase,
    "append_text": _append_text,
    "prepend_text": _prepend_text,
    "multiply": _multiply,
    "rename_key": _rename_key,
}


class TransformDataNode(BaseNode):
    node_type = "transform_data"

    def validate_config(self) -> None:
        required = {"transformation", "field"}
        missing = required - self.config.keys()
        if missing:
            raise ValueError(f"TransformDataNode missing config keys: {missing}")
        if self.config["transformation"] not in TRANSFORMS:
            raise ValueError(
                f"Unknown transformation '{self.config['transformation']}'. "
                f"Supported: {list(TRANSFORMS)}"
            )

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.validate_config()

        transformation: str = self.config["transformation"]
        field: str = self.config["field"]
        params: dict = self.config.get("params", {})

        if field not in payload:
            raise NodeExecutionError(
                f"TransformDataNode: field '{field}' not found in payload. "
                f"Available keys: {list(payload.keys())}"
            )

        transform_fn = TRANSFORMS[transformation]
        result = dict(payload)  # shallow copy — don't mutate input

        if transformation == "rename_key":
            new_key = params.get("new_key")
            if not new_key:
                raise NodeExecutionError(
                    "TransformDataNode: rename_key requires params.new_key"
                )
            result[new_key] = result.pop(field)
        else:
            result[field] = transform_fn(result[field], params)

        return result
