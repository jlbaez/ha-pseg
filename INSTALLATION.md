# PSEG Integration Installation Guide

This guide will walk you through installing and configuring the PSEG integration for Home Assistant.

## Prerequisites

- Home Assistant (Core, OS, or Supervised)
- PSEG  account with Smart Energy enabled
- Access to your Home Assistant configuration directory

## Installation Methods

### Method 1: HACS (Recommended)

1. **Install HACS** (if not already installed)

   - Follow the [HACS installation guide](https://hacs.xyz/docs/installation/installation/)
   - Restart Home Assistant after installation

2. **Add Custom Repository**

   - Go to **HACS** > **Integrations**
   - Click the three dots menu (⋮) in the top right
   - Select **Custom repositories**
   - Add repository: `https://github.com/yourusername/ha-psegli`
   - Category: **Integration**

3. **Install Integration**

   - Find "PSEG" in the HACS Integrations list
   - Click **Download**
   - Restart Home Assistant

4. **Configure Integration**
   - Go to **Settings** > **Devices & Services** > **Integrations**
   - Click **+ Add Integration**
   - Search for "PSEG" and select it
   - Follow the configuration wizard

### Method 2: Manual Installation

1. **Download Repository**

   ```bash
   git clone https://github.com/yourusername/ha-psegli.git
   ```

2. **Copy Integration Files**

   ```bash
   # Copy the integration to your custom_components directory
   cp -r ha-psegli/custom_components/psegli /path/to/homeassistant/config/custom_components/
   ```

3. **Restart Home Assistant**

   - Restart Home Assistant to load the new integration

4. **Configure Integration**
   - Go to **Settings** > **Devices & Services** > **Integrations**
   - Click **+ Add Integration**
   - Search for "PSEG" and select it
   - Follow the configuration wizard

## Configuration

### Initial Setup

1. **Add Integration**

   - Navigate to **Settings** > **Devices & Services** > **Integrations**
   - Click **+ Add Integration**
   - Search for "PSEG"

2. **Enter Credentials**

   - **Username**: Your PSEG account username/email
   - **Password**: Your PSEG account password
   - **Cookie** (Optional): If you have a valid cookie, enter it directly. If left empty, the integration will attempt to get one from the automation addon if available.

3. **Complete Setup**
   - Click **Submit** to complete the configuration
   - The integration will validate your credentials and cookie

### Cookie Management

The integration stores your authentication cookie and uses it for all API requests. When cookies expire:

1. **Automatic Refresh**: If the automation addon is available and healthy, the integration will automatically attempt to get a new cookie
2. **Manual Update**: Update the cookie via **Settings** > **Devices & Services** > **PSEG** > **Configure**
3. **Direct Input**: Manually obtain a cookie from your browser and enter it directly

### Options Flow

To update your configuration:

1. Go to **Settings** > **Devices & Services** > **PSEG**
2. Click **Configure**
3. **Update Cookie**: Enter a new cookie directly, or leave empty to attempt automatic refresh via addon
4. Click **Submit**

## Automation Addon (Optional)

The PSEG Automation Addon provides automatic cookie refresh capabilities:

### Addon Installation

1. **Install Addon**

   - Go to **Settings** > **Add-ons** > **Add-on Store**
   - Add the PSEG Automation repository
   - Install the addon

2. **Configure Addon**

   - Set your PSEG credentials in the addon configuration
   - Start the addon

3. **Integration Detection**
   - The integration will automatically detect and use the addon when available
   - No additional configuration required

## Verification

### Check Integration Status

1. **Integration Status**

   - Go to **Settings** > **Devices & Services** > **PSEG**
   - Status should show as "Configured"

2. **Data Availability**
   - Check the Home Assistant logs for successful data fetching
   - Look for PSEG data in the Energy Dashboard

### Test Services

1. **Manual Statistics Update**

   ```yaml
   service: psegli.update_statistics
   data:
     days_back: 0
   ```

2. **Check Logs**
   - Enable debug logging for the integration
   - Monitor logs for successful data retrieval

## Troubleshooting

### Common Issues

1. **Integration Won't Load**

   - Verify files are in the correct location
   - Check Home Assistant logs for errors
   - Restart Home Assistant

2. **Authentication Failed**

   - Verify your PSEG credentials
   - Check if your cookie is valid
   - Try updating the cookie manually

3. **No Data Available**
   - Ensure your PSEG account has Smart Energy enabled
   - Check if the integration is fetching data successfully
   - Verify the automation addon is running (if using)

### Debug Logging

Enable debug logging to troubleshoot issues:

```yaml
logger:
  custom_components.psegli: debug
```

### Getting Help

- Check the [README.md](README.md) for detailed information
- Review the Home Assistant logs for error messages
- Create an issue on the GitHub repository

## Next Steps

After successful installation:

1. **Monitor Data**: Check the Energy Dashboard for PSEG usage data
2. **Set Up Automations**: Create automations based on energy usage patterns
3. **Configure Notifications**: Set up alerts for high usage periods
4. **Explore Services**: Use the manual update service for data backfilling

## Support

For additional support:

- Review the troubleshooting section above
- Check the Home Assistant logs
- Create an issue on the GitHub repository
- Review the integration documentation

---

**Note**: This integration is designed to work independently without requiring the automation addon. The addon provides additional convenience for automatic cookie refresh but is not required for basic functionality.
