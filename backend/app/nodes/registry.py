"""
Node registry.

Maps node type strings → node classes.

To register a new node type, import its class and add one line here:
    NODE_REGISTRY["your_type"] = YourNodeClass
"""

from .base import BaseNode
from .manual_trigger import ManualTriggerNode
from .webhook_trigger import WebhookTriggerNode
from .transform_data import TransformDataNode
from .http_request import HttpRequestNode
from .send_email import SendEmailNode
from .wait_node import WaitNode
from .end_node import EndNode
from .decision import DecisionNode

NODE_REGISTRY: dict[str, type[BaseNode]] = {
    ManualTriggerNode.node_type: ManualTriggerNode,
    WebhookTriggerNode.node_type: WebhookTriggerNode,
    TransformDataNode.node_type: TransformDataNode,
    HttpRequestNode.node_type: HttpRequestNode,
    SendEmailNode.node_type: SendEmailNode,
    WaitNode.node_type: WaitNode,
    EndNode.node_type: EndNode,
    DecisionNode.node_type: DecisionNode,
}


def get_node(node_type: str, node_id: str, config: dict) -> BaseNode:
    """Instantiate a node by type string. Raises KeyError for unknown types."""
    cls = NODE_REGISTRY.get(node_type)
    if cls is None:
        raise KeyError(
            f"Unknown node type '{node_type}'. "
            f"Registered types: {list(NODE_REGISTRY)}"
        )
    return cls(node_id=node_id, config=config)
