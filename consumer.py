from kafka import KafkaConsumer
import psycopg2
import json

from dotenv import load_dotenv
import os

load_dotenv()

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "de_project")
POSTGRES_USER = os.getenv("POSTGRES_USER", "vedant")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "localdev")

conn = psycopg2.connect(
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD
)
cursor = conn.cursor()
consumer = KafkaConsumer(
    'orders',
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    auto_offset_reset='earliest'
)
print("Starting consumer... listening for orders")

for message in consumer:
    order = message.value
    print(f"Received: {order}")

    cursor.execute("""
        INSERT INTO raw_orders (order_id, customer_name, product, amount, event_timestamp)
        VALUES (%s, %s, %s, %s, to_timestamp(%s))
        ON CONFLICT (order_id) DO NOTHING
    """, (
        order['order_id'],
        order['customer_name'],
        order['product'],
        order['amount'],
        order['timestamp']
    ))
    conn.commit()