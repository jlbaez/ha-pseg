# PSEG Long Island Integration

A Home Assistant integration for monitoring energy usage from PSEG Long Island's Smart Energy program.

## Features

- **Real-time Energy Monitoring**: Track your daily, weekly, and monthly energy consumption
- **Peak vs Off-Peak Usage**: Monitor on-peak and off-peak energy usage patterns
- **Historical Data**: Access up to 2 years of historical usage data
- **Automatic Updates**: Data refreshes every 15 minutes
- **Statistics Integration**: Full integration with Home Assistant's Statistics API
- **Manual Refresh Service**: Service to manually update statistics and backfill historical data

## Installation

### Method 1: HACS (Recommended)

1. Install HACS if you haven't already
2. Add this repository as a custom repository in HACS
3. Install the "PSEG Long Island" integration
4. Restart Home Assistant
5. Go to **Settings** > **Devices & Services** > **Integrations**
6. Click **+ Add Integration** and search for "PSEG Long Island"

### Method 2: Manual Installation

1. Download this repository
2. Copy the `psegli` folder to your `custom_components` directory
3. Restart Home Assistant
4. Go to **Settings** > **Devices & Services** > **Integrations**
5. Click **+ Add Integration** and search for "PSEG Long Island"

## Configuration

### Initial Setup

1. **Add Integration**: Go to **Settings** > **Devices & Services** > **Integrations** and click **+ Add Integration**
2. **Search for PSEG**: Search for "PSEG Long Island" and select it
3. **Enter Credentials**:
   - **Username**: Your PSEG Long Island account username/email
   - **Password**: Your PSEG Long Island account password
   - **Cookie** (Optional): If you have a valid cookie, you can enter it directly. If left empty, the integration will attempt to get one from the automation addon if available.

### Cookie Management

The integration stores your authentication cookie and will use it for all API requests. When the cookie expires:

1. **Automatic Refresh**: If the automation addon is available and healthy, the integration will automatically attempt to get a new cookie
2. **Manual Update**: You can manually update the cookie by going to **Settings** > **Devices & Services** > **PSEG Long Island** > **Configure**
3. **Direct Cookie Input**: You can manually obtain a cookie from your browser and enter it directly

### Options Flow

To update your configuration:

1. Go to **Settings** > **Devices & Services** > **PSEG Long Island**
2. Click **Configure**
3. **Update Cookie**: Enter a new cookie directly, or leave empty to attempt automatic refresh via addon
4. Click **Submit**

## Services

### `psegli.update_statistics`

Manually update statistics with PSEG data. Useful for backfilling historical data.

**Service Data:**

- `days_back` (optional): Number of days back to fetch (default: 0, which means yesterday to today)

**Example:**

```yaml
# Update with today's data
service: psegli.update_statistics

# Update with last 7 days of data
service: psegli.update_statistics
data:
  days_back: 7
```

### `psegli.refresh_cookie`

Manually refresh the PSEG authentication cookie using the addon. Useful when you know your cookie has expired or you want to ensure fresh authentication.

**Service Data:**

No parameters required.

**Example:**

```yaml
# Refresh the authentication cookie
service: psegli.refresh_cookie
```

**Note:** This service requires the PSEG Long Island Automation Addon to be installed and running. If the addon is not available, you'll need to manually update your cookie in the integration settings.

## Data Structure

The integration provides the following data:

- **Off-Peak Usage**: Energy consumption during off-peak hours
- **On-Peak Usage**: Energy consumption during on-peak hours
- **Historical Data**: Up to 2 years of usage history
- **Real-time Updates**: Data refreshes every 15 minutes

## Troubleshooting

### Common Issues

1. **Authentication Failed**

   - Your cookie has expired
   - Go to **Settings** > **Devices & Services** > **PSEG Long Island** > **Configure**
   - Update your cookie or let the integration attempt automatic refresh

2. **No Data Available**

   - Check if your PSEG account has Smart Energy enabled
   - Verify your credentials are correct
   - Ensure your cookie is valid

3. **Integration Won't Load**
   - Check the Home Assistant logs for error messages
   - Verify the integration files are in the correct location
   - Restart Home Assistant

### Logs

Enable debug logging for the integration by adding this to your `configuration.yaml`:

```yaml
logger:
  custom_components.psegli: debug
```

## Automation Addon

This integration can optionally work with the PSEG Long Island Automation Addon to automatically refresh expired cookies. The addon is not required for the integration to function, but it provides:

- **Automatic Cookie Refresh**: Automatically obtains new cookies when they expire
- **Headless Operation**: No need to manually extract cookies from your browser
- **Reliable Authentication**: Maintains continuous access to your PSEG data

### Addon Setup

1. Install the PSEG Long Island Automation Addon from the addon store
2. Configure the addon with your credentials
3. Start the addon
4. The integration will automatically detect and use the addon when available

## Development

### Local Development

1. Clone this repository
2. Install development dependencies: `pip install -r requirements.txt`
3. Run tests: `python -m pytest`

### Contributing

1. Fork this repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:

- Create an issue on GitHub
- Check the troubleshooting section above
- Review the Home Assistant logs for error messages
