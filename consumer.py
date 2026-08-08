from kafka import KafkaConsumer
import psycopg2
import json
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="de_project",
    user="vedant",
    password="localdev"
)
cursor = conn.cursor()
consumer = KafkaConsumer(
    'orders',
    bootstrap_servers='localhost:9092',
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