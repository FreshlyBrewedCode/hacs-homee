from typing import List

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from pymee import Homee
from pymee.model import HomeeNode

from .const import CONF_GROUPS, DOMAIN


def get_imported_nodes(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> List[HomeeNode]:
    """Get a list of nodes that should be imported."""
    homee: Homee = hass.data[DOMAIN][config_entry.entry_id]
    all_groups = [str(g.id) for g in homee.groups]

    # Resolve the configured group ids to actual groups
    groups = [
        homee.get_group_by_id(int(g))
        for g in config_entry.options.get(CONF_GROUPS, all_groups)
    ]

    # Add all nodes from the groups in a list
    # Make sure each node is only added once
    nodes: List[HomeeNode] = []
    for g in groups:
        for n in g.nodes:
            if n not in nodes:
                nodes.append(n)

    return nodes
def has_attribute(node: HomeeNode, attributeType: int, readonly: bool = None):
    """Check if an attribute of the given type exists."""
    exists = attributeType in node._attribute_map

    if exists and readonly is not None:
        return is_readonly(node, attributeType) == readonly

    return exists


def is_readonly(node: HomeeNode, attributeType: int) -> bool:
    """Check if an attribute of the given type is readonly. Returns False if the attribute does not exist on the node."""
    attr = node.get_attribute_by_type(attributeType)
    if attr is not None:
        return attr.editable

    return False
