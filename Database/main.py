from kafka import KafkaConsumer
import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import json

# Kafka broker address and topic
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
TOPIC = os.getenv("TOPIC")

# InfluxDB connection details
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = os.getenv("DOCKER_INFLUXDB_INIT_ADMIN_TOKEN")
INFLUXDB_ORG = os.getenv("DOCKER_INFLUXDB_INIT_ORG")
INFLUXDB_BUCKET = os.getenv("DOCKER_INFLUXDB_INIT_BUCKET")

def create_consumer():
    # Create a Kafka consumer
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers = KAFKA_BROKER,
        auto_offset_reset = 'earliest',
        enable_auto_commit = True,
        group_id = 'influx',
        value_deserializer = lambda x: x.decode('utf-8')
    )

    return consumer

def save_to_influx(write_api, data):
    # Create an InfluxDB point with fields and tags from the cleaned data
    point = Point("market_data") \
        .tag("token", data['token']) \
        .field("end_time", data['end_time']) \
        .field("open_price", float(data['open_price'])) \
        .field("close_price", float(data['close_price'])) \
        .field("highest_price", float(data['highest_price'])) \
        .field("lowest_price", float(data['lowest_price'])) \
        .field("volume", float(data['volume'])) \
        .field("trades", int(data['trades'])) \
        .time(data['start_time'])

    # Write the point to InfluxDB
    write_api.write(bucket=INFLUXDB_BUCKET, record=point)

def main():
    consumer = create_consumer()

    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    while True:
        for message in consumer:
            try:
                converted = json.loads(message.value.replace("\'", "\""))
                print(f"Consumed: {converted}")
                save_to_influx(write_api, converted)
            except Exception as e:
                print("Error processing message:", e)

if __name__ == "__main__":
    main()