from fastapi import FastAPI, HTTPException, status
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os
import logging
from datetime import datetime  
from dotenv import load_dotenv

# Load .env early (safe even inside Docker if file is present)
load_dotenv()
# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logging.debug("Starting main.py")

# Print key environment variables to debug
for var in [
    "DHW_INFLUXDB_URL", "DHW_INFLUXDB_TOKEN", "DHW_INFLUXDB_ORG",
    "DHW_INFLUXDB_BUCKET", "DHW_INFLUXDB_MEASUREMENT", "DHW_INFLUXDB_TEMP_FIELD"
]:
    val = os.getenv(var)
    masked = "********" if "TOKEN" in var and val else val
    logging.debug(f"ENV {var} = {masked}")

app = FastAPI()

# InfluxDB Configuration (Use environment variables for security)
DHW_INFLUXDB_URL = os.getenv("DHW_INFLUXDB_URL")
DHW_INFLUXDB_TOKEN = os.environ.get("DHW_INFLUXDB_TOKEN")
DHW_INFLUXDB_ORG = os.environ.get("DHW_INFLUXDB_ORG")
DHW_INFLUXDB_BUCKET = os.environ.get("DHW_INFLUXDB_BUCKET", "altherma")  # Default to 'altherma'
DHW_INFLUXDB_MEASUREMENT = os.environ.get("DHW_INFLUXDB_MEASUREMENT", "altherma")  # Default to 'altherma'
DHW_INFLUXDB_TEMP_FIELD = os.environ.get("DHW_INFLUXDB_TEMP_FIELD", "DHW_tank_temp_(R5T)")  # Default to DHW field

# Log the values of the environment variables
masked_token = "********" if DHW_INFLUXDB_TOKEN else DHW_INFLUXDB_TOKEN
logging.info(f"DHW_INFLUXDB_TOKEN: {masked_token}")
logging.info(f"DHW_INFLUXDB_ORG: {DHW_INFLUXDB_ORG}")
logging.info(f"DHW_INFLUXDB_BUCKET: {DHW_INFLUXDB_BUCKET}")
logging.info(f"DHW_INFLUXDB_MEASUREMENT: {DHW_INFLUXDB_MEASUREMENT}")
logging.info(f"DHW_INFLUXDB_TEMP_FIELD: {DHW_INFLUXDB_TEMP_FIELD}")


# Initialize InfluxDB client and query API
client = None  # Initialize as None for handling potential connection errors
query_api = None

try:
    logging.debug("Initializing InfluxDB client")
    client = InfluxDBClient(
        url=DHW_INFLUXDB_URL,
        token=DHW_INFLUXDB_TOKEN,
        org=DHW_INFLUXDB_ORG
    )
    query_api = client.query_api()
    logging.info("Successfully connected to InfluxDB.")
except Exception as e:
    logging.error(f"Failed to connect to InfluxDB: {e}")
    # Consider exiting or handling the error appropriately if InfluxDB connection is essential.
    # For example:
    # raise SystemExit("Could not connect to InfluxDB. Exiting.")


def get_minutes_left():
    """
    Hardcoded function to return estimated minutes of hot water remaining (for now).
    """
    return 30

@app.get("/dhw", response_model=None)
async def get_dhw_status():
    """
    Returns the current DHW status, including:
    - Current temperature
    - Estimated minutes left
    - Availability
    - Whether DHW is currently being heated
    - Historical DHW temperatures (one per minute for last 30 minutes)
    """
    try:
        if query_api is None:
            raise Exception("InfluxDB query API not initialized.")

        # -------------------------------
        # 🔹 Query 1: Latest Temperature
        # -------------------------------
        temp_query = f"""
        from(bucket: "{DHW_INFLUXDB_BUCKET}")
          |> range(start: -5m)
          |> filter(fn: (r) => r._measurement == "{DHW_INFLUXDB_MEASUREMENT}")
          |> filter(fn: (r) => r._field == "{DHW_INFLUXDB_TEMP_FIELD}")
          |> last()
        """
        logging.info(f"Executing temperature query: {temp_query}")
        temp_result = query_api.query(org=DHW_INFLUXDB_ORG, query=temp_query)

        temperature = None
        if temp_result and len(temp_result) > 0 and temp_result[0].records:
            temperature = float(temp_result[0].records[0].get_value())
            logging.info(f"DHW Temperature: {temperature}")
        else:
            logging.warning("No DHW temperature data found.")

        available = temperature is not None
        minutes_left = get_minutes_left()

        # -------------------------------
        # 🔹 Query 2: Operation Mode + Valve State
        # -------------------------------
        logic_query = f"""
        from(bucket: "{DHW_INFLUXDB_BUCKET}")
          |> range(start: -1h)
          |> filter(fn: (r) => r._measurement == "{DHW_INFLUXDB_MEASUREMENT}")
          |> filter(fn: (r) => r._field == "Operation_Mode" or r._field == "3way_valve(On:DHW_Off:Space)")
          |> last()
        """
        logging.info(f"Executing logic query: {logic_query}")
        logic_result = query_api.query(org=DHW_INFLUXDB_ORG, query=logic_query)

        operation_mode = None
        valve_state = None

        for table in logic_result:
            for record in table.records:
                field = record.get_field()
                value = record.get_value()
                if field == "Operation_Mode":
                    operation_mode = str(value)
                elif field == "3way_valve(On:DHW_Off:Space)":
                    try:
                        valve_state = int(value)
                    except ValueError:
                        valve_state = None

        heating_dhw = operation_mode == "Heating" and valve_state == 1
        logging.info(f"Operation_Mode: {operation_mode}, Valve State: {valve_state}, Heating DHW: {heating_dhw}")

        # -------------------------------
        # 🔹 Query 3: Historical Temperatures (last 30 min, 1 per minute)
        # -------------------------------
        historical_query = f"""
        from(bucket: "{DHW_INFLUXDB_BUCKET}")
          |> range(start: -30m)
          |> filter(fn: (r) => r._measurement == "{DHW_INFLUXDB_MEASUREMENT}")
          |> filter(fn: (r) => r._field == "{DHW_INFLUXDB_TEMP_FIELD}")
          |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
          |> yield(name: "mean")
        """
        logging.info(f"Executing historical query: {historical_query}")
        historical_result = query_api.query(org=DHW_INFLUXDB_ORG, query=historical_query)

        dhw_historical = []
        for table in historical_result:
            for record in table.records:
                timestamp = int(record.get_time().timestamp())  # convert to UNIX seconds
                value = float(record.get_value())
                dhw_historical.append({
                    "dt": timestamp,
                    "temp": value
                })

        # -------------------------------
        # 🔹 Final Response
        # -------------------------------
        response_data = {
            "temperature": temperature,
            "minutes_left": minutes_left,
            "available": available,
            "heating_dhw": heating_dhw,
            "dhw_historical": dhw_historical
        }

        logging.info(f"DHW response: {response_data}")
        return response_data

    except Exception as e:
        logging.error(f"Error fetching DHW status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Endpoint for health checks. Returns a 200 OK status if the service is up and running.
    """
    return {"status": "ok"}


if __name__ == "__main__":
    try:
        import uvicorn
        logging.debug("Launching FastAPI app with Uvicorn")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logging.critical(f"FastAPI app crashed: {e}", exc_info=True)
