SELECT
    o.order_id,
    c.customer_id,
    o.product,
    o.order_amount,
    o.event_timestamp
FROM {{ref ('stg_orders') }}  o
LEFT JOIN {{ref ('dim_customers')}}  c
    ON o.customer_name = c.customer_name