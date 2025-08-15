import logging
import os
from time import sleep
import psycopg2 as db
from typing import List, Mapping
from datetime import datetime, timezone
from dotenv import load_dotenv

from snmp import Engine, SNMPv1

# Load variables from .env into environment
load_dotenv()

# Configure logging — only errors, only to file, no console
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=os.path.join(os.getcwd(), "error.log"),
    filemode="a",  # append mode; use "w" to overwrite each run
)

POLL_INTERVAL_SEC = 10
SENSOR_IP = os.getenv("SENSOR_IP")
SNMP_COMMUNITY = os.getenv("SNMP_COMMUNITY").encode("ascii")

OIDS: Mapping[str, str] = {
    "Temperature": "1.3.6.1.4.1.21796.4.1.3.1.5.1",
    "Humidity": "1.3.6.1.4.1.21796.4.1.3.1.5.2",
}


def push_to_db() -> None:
    conn = None  # Initialize conn to None
    try:
        conn = db.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
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
            """
        )

        ts = datetime.now(timezone.utc)
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
        logging.error(f"Database error: {err}")
    finally:
        if conn is not None:
            conn.close()


def fetch_data(oids) -> List[float]:
    data = []

    for _, oid in oids.items():
        try:
            with Engine(SNMPv1, defaultCommunity=SNMP_COMMUNITY) as engine:
                mgr = engine.Manager(SENSOR_IP, community=SNMP_COMMUNITY)
                resp = mgr.get(oid)
                oid, value = resp[0]
                data.append(value.value * 0.1)
       
        except Exception as err:
            logging.error(f"SNMP error for OID {oid}: {err}")

    return data


if __name__ == "__main__":
    while True:
        push_to_db()
        sleep(POLL_INTERVAL_SEC)
