from kafka import KafkaProducer
from faker import Faker
import json
import time
import random
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
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