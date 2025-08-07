# PSEG Long Island Integration for Home Assistant

This integration provides real-time energy usage data from PSEG Long Island to Home Assistant.

## Features

- **Off-Peak Usage**: Real-time off-peak energy usage (15-minute intervals)
- **On-Peak Usage**: Real-time on-peak energy usage (15-minute intervals)
- **Energy Dashboard Compatible**: Includes sensors designed for Home Assistant's Energy Dashboard

## Installation

### Method 1: Manual Installation

1. Download this integration
2. Copy the `psegli` folder to your `config/custom_components/` directory
3. Restart Home Assistant

### Method 2: HACS (Recommended)

1. Add this repository to HACS
2. Install the integration
3. Restart Home Assistant

## Configuration

### Step 1: Get Your Authentication Cookie

1. Go to [PSEG MyAccount](https://id.myaccount.psegliny.com/)
2. Log in to your account
3. Open your browser's Developer Tools (F12)
4. Go to the Network tab
5. Navigate to the MySmartEnergy dashboard
6. Find a request to `mysmartenergy.psegliny.com`
7. Copy the `Cookie` header value

### Step 2: Add the Integration

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "PSEG Long Island"
4. Enter your authentication cookie
5. Click **Submit**

## Energy Dashboard Integration

This integration is fully compatible with Home Assistant's Energy Dashboard. The `sensor.pseg_total_energy_consumption` sensor is specifically designed for the Energy Dashboard and includes:

- **Device Class**: `energy`
- **State Class**: `total`
- **Unit**: `kWh`
- **Display Precision**: 2 decimal places

To add it to your Energy Dashboard:

1. Go to **Settings** → **Dashboards** → **Energy**
2. Click **Add Consumption**
3. Select `sensor.pseg_total_energy_consumption`
4. Configure your energy rates and billing cycle

## Troubleshooting

### Invalid Authentication Error

- Make sure your cookie is current and valid
- Try logging out and back in to PSEG to get a fresh cookie
- Check that you're copying the entire cookie value

### No Data Available

- The integration updates every 5 minutes
- Check that your PSEG account has access to MySmartEnergy
- Verify your cookie is still valid

### Energy Dashboard Not Working

- Ensure you're using `sensor.pseg_total_energy_consumption` for the Energy Dashboard
- The sensor must have `total` state class and `energy` device class (already configured)
- Check that the sensor is receiving data before adding to Energy Dashboard

## Support

For issues and feature requests, please create an issue on the GitHub repository.

## License

This project is licensed under the MIT License.
