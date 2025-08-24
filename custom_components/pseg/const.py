"""Constants for the PSEG integration."""

DOMAIN = "pseg"

# Defaults
DEFAULT_NAME = "PSEG"
DEFAULT_SCAN_INTERVAL = 300  # 5 minutes

# Configuration
CONF_COOKIE = "cookie"
CONF_URL_ROOT = "url_root"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# Addon configuration
CONF_ADDON_URL = "addon_url"
DEFAULT_ADDON_URL = "http://localhost:8000"

# Sensor names
SENSOR_TOTAL_ENERGY = "total_energy"
SENSOR_DAILY_USAGE = "daily_usage"
SENSOR_WEEKLY_USAGE = "weekly_usage"
SENSOR_CURRENT_USAGE = "current_usage"
SENSOR_OFF_PEAK_USAGE = "off_peak_usage"
SENSOR_ON_PEAK_USAGE = "on_peak_usage"
SENSOR_TEMPERATURE = "temperature"

# Sensor attributes
ATTR_LAST_UPDATE = "last_update"
ATTR_COMPARISON = "comparison"
ATTR_DESCRIPTION = "description" 
