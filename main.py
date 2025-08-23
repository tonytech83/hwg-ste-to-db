import datetime
import logging
from collections.abc import Mapping
from pathlib import Path
from time import sleep

from dotenv import dotenv_values
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from snmp import Engine, SNMPv1

ENV_PATH = Path() / ".env"  # points to ./.env
LOG_PATH = Path() / "error.log"  # points to ./error.log

# Configure logging — only errors, only to file, no console
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=(LOG_PATH).resolve(),
    filemode="a",  # append mode; use "w" to overwrite each run
)

# load env values into a dict
config = dotenv_values(ENV_PATH)

POLL_INTERVAL_SEC = 60
SENSOR_IP = config.get("SENSOR_IP")
SNMP_COMMUNITY = config.get("SNMP_COMMUNITY").encode("ascii")

OIDS: Mapping[str, str] = {
    "Temperature": "1.3.6.1.4.1.21796.4.1.3.1.5.1",
    "Humidity": "1.3.6.1.4.1.21796.4.1.3.1.5.2",
}


def push_to_db() -> None:
    client = None
    try:
        # Create InfluxDB client
        client = InfluxDBClient(
            url=config.get("INFLUX_URL"),
            token=config.get("INFLUX_TOKEN"),
            org=config.get("INFLUX_ORG"),
        )

        write_api = client.write_api(write_options=SYNCHRONOUS)

        # Get current timestamp
        ts = datetime.datetime.now(datetime.UTC)

        # Fetch sensor data
        temperature, humidity = fetch_data(OIDS)

        # Create data point
        point = (
            Point("sensor_data")
            .tag("sensor_ip", SENSOR_IP)
            .tag(
                "location", config.get("SENSOR_LOCATION", "unknown")
            )  # optional location tag
            .field("temperature_c", float(temperature))
            .field("humidity_rh", float(humidity))
            .time(ts, WritePrecision.S)
        )

        # Write to InfluxDB
        write_api.write(
            bucket=config.get("INFLUX_BUCKET"),
            org=config.get("INFLUX_ORG"),
            record=point,
        )
        # logging.info(f"Data written: temp={temperature}°C, humidity={humidity}%RH")

    except Exception as err:
        logging.exception(f"InfluxDB error: {err}")
    finally:
        if client is not None:
            client.close()


def fetch_data(oids):
    data = []

    for oid in oids.values():
        try:
            with Engine(SNMPv1, defaultCommunity=SNMP_COMMUNITY) as engine:
                mgr = engine.Manager(SENSOR_IP, community=SNMP_COMMUNITY)
                resp = mgr.get(oid)
                _, value = resp[0]
                data.append(value.value * 0.1)

        except Exception as err:
            logging.exception(f"SNMP error for OID {oid}: {err}")

    return data


if __name__ == "__main__":
    while True:
        push_to_db()
        sleep(POLL_INTERVAL_SEC)
