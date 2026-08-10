SELECT
    order_id,
    customer_name,
    product,
    amount as order_amount,
    event_timestamp,
    ingested_at
FROM {{source ('raw', 'raw_orders')}}
WHERE amount > 0

