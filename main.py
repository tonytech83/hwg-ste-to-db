import datetime
import logging
from collections.abc import List, Mapping
from pathlib import Path
from time import sleep

import psycopg2 as db
from dotenv import dotenv_values
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

POLL_INTERVAL_SEC = 10
SENSOR_IP = config.get("SENSOR_IP")
SNMP_COMMUNITY = config.get("SNMP_COMMUNITY").encode("ascii")

OIDS: Mapping[str, str] = {
    "Temperature": "1.3.6.1.4.1.21796.4.1.3.1.5.1",
    "Humidity": "1.3.6.1.4.1.21796.4.1.3.1.5.2",
}


def push_to_db() -> None:
    conn = None  # Initialize conn to None
    try:
        conn = db.connect(
            dbname=config.get("DB_NAME"),
            user=config.get("DB_USER"),
            password=config.get("DB_PASSWORD"),
            host=config.get("DB_HOST"),
            port=config.get("DB_PORT"),
        )
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_data (
                id BIGSERIAL PRIMARY KEY,
                ts TIMESTAMPTZ NOT NULL DEFAULT now(),
                temperature_c NUMERIC(5, 2) NOT NULL,
                humidity_rh NUMERIC(5, 2) NOT NULL,
                CHECK (humidity_rh BETWEEN 0 AND 100)
            )
            """,
        )

        ts = datetime.now(datetime.UTC)
        temperature, humidity = fetch_data(OIDS)

        cursor.execute(
            """
            INSERT INTO sensor_data (ts, temperature_c, humidity_rh)
            VALUES(%s, %s, %s)
            """,
            (ts, temperature, humidity),
        )

        conn.commit()
    except db.Error as err:
        logging.exception(f"Database error: {err}")
    finally:
        if conn is not None:
            conn.close()


def fetch_data(oids) -> List[float]:
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
