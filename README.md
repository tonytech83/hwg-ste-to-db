# HWg-STE: SNMP Thermometer - Data Collector

A Python application that collects temperature and humidity data from [HWg-STE: SNMP Thermometer](https://www.hw-group.com/device/hwg-ste) and stores it in a PostgreSQL database.

## Features

- SNMP data collection from **HWg-STE: SNMP Thermometer**
- PostgreSQL database storage
- Docker support
- Configurable polling interval
- Automatic table creation

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL database
- HWg-STE: SNMP Thermometer

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Sensor Configuration
SENSOR_IP=your_ip_address
SNMP_COMMUNITY=your_community_string # default is "public"

# Database Configuration
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=your_host
DB_PORT=your_port # default is 5432
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

## Database Schema

The application creates a `sensor_data` table with:
- `id`: Primary key
- `ts`: Timestamp (UTC)
- `temperature_c`: Temperature in Celsius
- `humidity_rh`: Humidity percentage (0-100)

## Configuration

- `POLL_INTERVAL_SEC`: Data collection interval (default: 10 seconds)
- SNMP OIDs are configured for temperature and humidity sensors
