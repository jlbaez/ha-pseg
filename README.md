# PSEG Long Island Home Assistant Integration

A Home Assistant custom integration for PSEG Long Island that provides energy usage data using Home Assistant's Statistics API (similar to Opower).

## Features

- **Statistics-Based System**: Writes data directly into Home Assistant's long-term statistics system
- **Automatic Updates**: Automatically fetches and updates data every 15 minutes
- **Manual Backfilling**: Service for manually backfilling historical data
- **Proper Time Alignment**: Data is backdated to the correct timestamps
- **Energy Dashboard Compatible**: Works seamlessly with Home Assistant's Energy Dashboard
- **Secure Authentication**: Supports both direct UI input and secure secrets.yaml storage

## How It Works (Like Opower)

Home Assistant's energy dashboard is designed to work with historical, finalized energy data, not real-time streaming. This integration follows the same model as Opower:

- **Statistics-Based System**: Data is recorded in kWh for specific time periods (hourly)
- **Proper Time Alignment**: Even though data arrives late, it is backdated to the correct day
- **No Real-Time Monitoring**: Cannot show current power (in W or kW) or hour-by-hour usage for today
- **Only Historical Data**: Fills in past days/months with accurate, utility-verified totals

## Installation

### Option 1: Manual Installation

1. Download this repository
2. Copy the `custom_components/psegli` folder to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Add the integration through the UI

### Option 2: HACS (Recommended)

1. Add this repository to HACS
2. Install the integration
3. Restart Home Assistant
4. Add the integration through the UI

## Configuration

### Step 1: Get Your PSEG Cookie

1. Go to [PSEG MyAccount](https://id.myaccount.psegliny.com/)
2. Log in to your account
3. Open your browser's Developer Tools (F12)
4. Go to the Network tab
5. Navigate to the MySmartEnergy dashboard
6. Find a request to `mysmartenergy.psegliny.com`
7. Copy the `Cookie` header value

### Step 2a (Optional): Add Cookie to secrets.yaml (Recommended for Security)

If you want to store your cookie securely, add it to your `config/secrets.yaml`:

```yaml
psegli_cookie: "MM_SID=your_cookie_value_here; __RequestVerificationToken=your_token_here"
```

### Step 2: Add the Integration

**Important**: This integration uses UI-based configuration only. Do not add any YAML configuration for this integration.

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "PSEG Long Island"
4. Enter your authentication cookie in one of two ways:
   - **Option A (Direct)**: Paste your cookie directly in the UI
   - **Option B (Secure)**: Add your cookie to `secrets.yaml` and reference it as `!secret psegli_cookie`
5. Click **Submit**

## Available Statistics

The integration creates the following statistics entries (visible in the Energy Dashboard):

- `psegli:off_peak_usage`: Off-peak energy usage in kWh
- `psegli:on_peak_usage`: On-peak energy usage in kWh

**Note**: These are statistics entries, not sensors. They appear in the Energy Dashboard configuration and show historical data with proper timestamps.

## Updating Your Cookie

When your cookie expires (you'll get a notification in Home Assistant), you can easily update it:

1. Go to **Settings** → **Devices & Services**
2. Find **PSEG Long Island** integration
3. Click **Configure**
4. Enter your new cookie (follow the same steps as initial setup to get a fresh cookie)
5. Click **Submit**

The integration will automatically reload with the new cookie and clear any expiration notifications.

## Services

### `psegli.update_statistics`

This service allows manual backfilling of historical data. It's useful for:

- Initial setup to populate historical data
- Manual updates when needed
- Backfilling specific time periods

**Parameters:**

- `days_back` (optional): Number of days of historical data to fetch (default: 0)
  - `0`: Latest data only (for real-time updates)
  - `1`: 1 day of historical data (for hourly updates)
  - `30`: 30 days of historical data (for monthly backfills)

**Usage:**

```yaml
# Update with latest data only
service: psegli.update_statistics
data:
  days_back: 0

# Backfill with 30 days of historical data
service: psegli.update_statistics
data:
  days_back: 30

# Or use the automation examples in automation_example.yaml
```

## Automatic Updates

The integration automatically updates statistics every 15 minutes with the latest data from PSEG. No user intervention is required.

## Energy Dashboard Setup

1. Go to **Settings** → **Dashboards** → **Energy**
2. Click **Add Consumption**
3. Select either:
   - `psegli:off_peak_usage` for off-peak energy
   - `psegli:on_peak_usage` for on-peak energy
4. The data will appear in your Energy Dashboard with proper historical timestamps

## Testing

You can test the integration before installing it in Home Assistant:

1. Replace `YOUR_COOKIE_HERE` in `test_psegli_standalone.py` with your actual cookie
2. Run: `python test_psegli_standalone.py`

## Troubleshooting

### Invalid Authentication

- Make sure your cookie is current and valid
- Try logging out and back in to PSEG to get a fresh cookie
- Check that you're copying the entire cookie value

### No Data Available

- The integration updates automatically every 15 minutes
- Check that your PSEG account has access to MySmartEnergy
- Verify your cookie is still valid
- Try the manual service call to backfill data

### Secret Not Found Error

- Make sure your `secrets.yaml` file exists in your config directory
- Verify the secret name matches exactly (e.g., `psegli_cookie`)
- Check that the secret name in the UI matches the key in `secrets.yaml`
- Restart Home Assistant after adding secrets to `secrets.yaml`

### Integration Not Found

- Make sure you've copied the files to the correct location
- Restart Home Assistant after adding the files
- Check the Home Assistant logs for any errors

## Development

### Project Structure

```
custom_components/psegli/
├── __init__.py              # Main integration setup (statistics only)
├── manifest.json            # Integration metadata
├── config_flow.py           # Configuration flow
├── const.py                 # Constants
├── exceptions.py            # Custom exceptions
├── psegli.py               # PSEG API client
├── translations/           # UI translations
│   └── en/
│       └── config_flow.json
└── services.yaml           # Service definitions
```

### Key Design Decisions

- **Statistics-Only**: No sensors, only statistics entries (like Opower)
- **Automatic Updates**: Runs every 15 minutes without user intervention
- **Manual Service**: Available for backfilling and manual updates
- **Proper Time Alignment**: Data is backdated to correct timestamps
- **Energy Dashboard Focus**: Designed specifically for Energy Dashboard compatibility

## License

This project is licensed under the MIT License - see the LICENSE file for details.
