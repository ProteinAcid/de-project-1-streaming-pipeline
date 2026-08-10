SELECT
    ROW_NUMBER() OVER (ORDER BY customer_name) AS customer_id,
    customer_name,
    COUNT(*) AS total_orders,
    SUM(order_amount) AS lifetime_value,
    MIN(event_timestamp) AS first_order_date,
    MAX(event_timestamp) AS most_recent_order_date
FROM {{ ref('stg_orders') }}
GROUP BY customer_name