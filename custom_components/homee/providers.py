import logging

from .const import NodeProfileNames
from .registry import HomeeEntityEntry, homee_entity_provider, HomeeEntityProvider
from .helpers import has_attribute

from pymee.model import HomeeNode
from pymee.const import NodeProfile, AttributeType

_LOGGER = logging.getLogger(__name__)


@homee_entity_provider
class HomeeLightProvider(HomeeEntityProvider):
    def __init__(self, registry) -> None:
        super().__init__(registry)

    def provide(self, node: HomeeNode):

        # 1. Node is clearly a light because it has an explicit light profile
        if node.profile in [
            NodeProfile.DIMMABLE_LIGHT,
            NodeProfile.DIMMABLE_COLOR_LIGHT,
            NodeProfile.DIMMABLE_EXTENDED_COLOR_LIGHT,
            NodeProfile.DIMMABLE_COLOR_TEMPERATURE_LIGHT,
            NodeProfile.DIMMABLE_LIGHT_WITH_BRIGHTNESS_SENSOR,
            NodeProfile.DIMMABLE_LIGHT_WITH_BRIGHTNESS_AND_PRESENCE_SENSOR,
            NodeProfile.DIMMABLE_LIGHT_WITH_PRESENCE_SENSOR,
        ]:
            return [HomeeEntityEntry("light", node)]

        # 2. Node has ON/OFF and editable BRIGHTNESS attribute
        if has_attribute(node, AttributeType.ON_OFF) and has_attribute(
            node, AttributeType.BRIGHTNESS, readonly=False
        ):
            return [HomeeEntityEntry.light(node)]

        return []