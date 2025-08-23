# HWg-STE: SNMP Thermometer - Data Collector

A Python application that collects temperature and humidity data from [HWg-STE: SNMP Thermometer](https://www.hw-group.com/device/hwg-ste) and stores it in a InfluxDB database.

## Features

- SNMP data collection from **HWg-STE: SNMP Thermometer**
- InfluxDB database
- Docker support
- Configurable polling interval

## Setup

### Prerequisites

- Python 3.11+
- UInfluxDB database
- HWg-STE: SNMP Thermometer

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Sensor Configuration
SENSOR_IP=<your_ip_address>
SNMP_COMMUNITY=<your_community_string> # default is "public"

# InfluxDB2 settings
INFLUX_URL=<your_host>
INFLUX_TOKEN=<your_token>
INFLUX_ORG=<your_org>
INFLUX_BUCKET=<your_bucket>

# Optional
SENSOR_LOCATION=<your_location>  # adds location tag for better querying
```

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

### Docker

```bash
docker build -t sensor-collector .
docker run --env-file .env sensor-collector
```

## Configuration

- `POLL_INTERVAL_SEC`: Data collection interval (default: 60 seconds)
- SNMP OIDs are configured for temperature and humidity sensors
