"""Constants for the homee integration."""

# General
DOMAIN = "homee"

# Cubes
BRAIN_CUBE = "Brain Cube"
ZWAVE_CUBE = "Z-Wave Cube"
ZIGBEE_CUBE = "Zigbee Cube"
ENOCEAN_CUBE = "EnOcean Cube"


# Services
SERVICE_SET_VALUE = "set_value"

# Attributes
ATTR_NODE = "node"
ATTR_ATTRIBUTE = "attribute"
ATTR_VALUE = "value"

HOMEE_LIGHT_MIN_MIRED = 153
HOMEE_LIGHT_MAX_MIRED = 556

# Options
CONF_INITIAL_OPTIONS = "initial_options"
CONF_ADD_HOME_DATA = "add_homee_data"
CONF_GROUPS = "groups"
CONF_WINDOW_GROUPS = "window_groups"
CONF_DOOR_GROUPS = "door_groups"

# Other
UNKNOWN_MANUFACTURER = "-"
UNKNOWN_MODEL = "-"

# TODO: Move NodeProfileNames to pymee
NodeProfileNames = {
    0: "None",
    1: "Homee",
    10: "On Off Plug",
    11: "Dimmable Metering Switch",
    12: "Metering Switch",
    13: "Metering Plug",
    14: "Dimmable Plug",
    15: "Dimmable Switch",
    16: "On Off Switch",
    18: "Double On Off Switch",
    19: "Dimmable Metering Plug",
    20: "One Button Remote",
    21: "Binary Input",
    22: "Dimmable Color Metering Plug",
    23: "Double Binary Input",
    24: "Two Button Remote",
    25: "Three Button Remote",
    26: "Four Button Remote",
    27: "Alarm Sensor",
    28: "Double On Off Plug",
    29: "On Off Switch With Binary Input",
    30: "Watch Dog With Pressure And Temperatures",
    31: "Fibaro Button",
    32: "Energy Meter",
    33: "Double Metering Switch",
    34: "Fibaro Swipe",
    38: "Energy Manager",
    39: "Level Meter",
    40: "Range Extender",
    41: "Remote",
    42: "Impulse Plug",
    43: "Impulse Relay",
    1e3: "Brightness Sensor",
    1001: "Dimmable Color Light",
    1002: "Dimmable Extended Color Light",
    1003: "Dimmable Color Temperature Light",
    1004: "Dimmable Light",
    1005: "Dimmable Light With Brightness Sensor",
    1006: "Dimmable Light With Brightness And Presence Sensor",
    1007: "Dimmable Light With Presence Sensor",
    1008: "Dimmable Rgbwlight",
    2e3: "Open Close Sensor",
    2001: "Window Handle",
    2002: "Shutter Position Switch",
    2003: "Open Close And Temperature Sensor",
    2004: "Electric Motor Metering Switch",
    2005: "Open Close With Temperature And Brightness Sensor",
    2006: "Electric Motor Metering Switch Without Slat Position",
    2007: "Lock",
    2008: "Window Handle With Buttons",
    2009: "Window Handle With Buttons And Temperature And Humidity Sensor",
    2010: "Entrance Gate Operator",
    2011: "Perimeter Protection System",
    2012: "Garage Door Operator",
    2013: "Gate Operator",
    2014: "Inner Door Operator",
    2015: "Garage Door Impulse Operator",
    3001: "Temperature And Humidity Sensor",
    3002: "Co2sensor",
    3003: "Room Thermostat",
    3004: "Room Thermostat With Humidity Sensor",
    3005: "Binary Input With Temperature Sensor",
    3006: "Radiator Thermostat",
    3009: "Temperature Sensor",
    3010: "Humidity Sensor",
    3011: "Water Valve",
    3012: "Water Meter",
    3013: "Weather Station",
    3014: "Netatmo Main Module",
    3015: "Netatmo Outdoor Module",
    3016: "Netatmo Indoor Module",
    3017: "Netatmo Rain Module",
    3018: "Cosi Therm Channel",
    3019: "Ventilation Control",
    3022: "Thermostat With Heating And Cooling",
    3023: "Netatmo Wind Module",
    3024: "Electrical Heating",
    3025: "Valve Drive",
    3026: "Camera",
    3027: "Camera With Floodlight",
    3028: "Heating System",
    3029: "Warm Water Circuit",
    3030: "Heating Circuit",
    4010: "Motion Detector With Temperature Brightness And Humidity Sensor",
    4011: "Motion Detector",
    4012: "Smoke Detector",
    4013: "Flood Detector",
    4014: "Presence Detector",
    4015: "Motion Detector With Temperature And Brightness Sensor",
    4016: "Smoke Detector With Temperature Sensor",
    4017: "Flood Detector With Temperature Sensor",
    4018: "Watch Dog Device",
    4019: "Lag",
    4020: "Owu",
    4021: "Eurovac",
    4022: "Owwg3",
    4023: "Europress",
    4024: "Minimum Detector",
    4025: "Maximum Detector",
    4026: "Smoke Detector And Codetector",
    4027: "Siren",
    4028: "Motion Detector With Open Close Temperature And Brightness Sensor",
    4029: "Motion Detector With Brightness",
    4030: "Doorbell",
    4031: "Smoke Detector And Siren",
    4032: "Flood Detector With Temperature And Humidity Sensor",
    4033: "Minimum Detector With Temperature Sensor",
    4034: "Maximum Detector With Temperature Sensor",
    4035: "Presence Detector With Temperature And Brightness Sensor",
    4036: "Codetector",
    5e3: "Inova Alarm System",
    5001: "Inova Detector",
    5002: "Inova Siren",
    5003: "Inova Command",
    5004: "Inova Transmitter",
    5005: "Inova Reciever",
    5006: "Inova Koala",
    5007: "Inova Internal Transmitter",
    5008: "Inova Control Panel",
    5009: "Inova Input Output Extension",
    5010: "Inova Motion Detector With Vod",
    5011: "Inova Motion Detector",
    6e3: "Washing Machine",
    6001: "Tumble Dryer",
    6002: "Dishwasher",
}