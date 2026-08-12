from kafka import KafkaProducer
from faker import Faker
import json
import time
import random

from dotenv import load_dotenv
import os

load_dotenv()

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")

producer = KafkaProducer(
    bootstrap_servers= KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
fake = Faker()

print("Starting order event producer... press Ctrl+C to stop")

while True:
    order_event = {
        "order_id": fake.uuid4(),
        "customer_name": fake.name(),
        "product": fake.word(),
        "amount": round(random.uniform(5, 500), 2),
        "timestamp": time.time()
    }

    producer.send('orders', value=order_event)
    print(f"Sent: {order_event}")

    time.sleep(random.uniform(1, 3))