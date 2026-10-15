-- Delivery performance by purchase month.
-- Include delivered orders with valid delivery endpoints.
-- Calculate delivery duration in elapsed days.
-- Compare calendar dates to identify late deliveries.

WITH eligible_orders AS (
    SELECT
        DATE_TRUNC(
            'month', order_purchase_timestamp
        )::DATE AS purchase_month,
        EXTRACT(
            EPOCH FROM (
                order_delivered_customer_date
                - order_purchase_timestamp
            )
        ) / 86400.0 AS delivery_days,
        order_delivered_customer_date::DATE
            - order_estimated_delivery_date::DATE
            AS days_after_estimate
    FROM public.orders
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
      AND order_delivered_customer_date >= order_purchase_timestamp
)
SELECT
    purchase_month,
    COUNT(*) AS eligible_orders,
    ROUND(AVG(delivery_days), 2) AS average_delivery_days,
    ROUND(
        (
            PERCENTILE_CONT(0.5)
            WITHIN GROUP (ORDER BY delivery_days)
        )::NUMERIC,
        2
    ) AS median_delivery_days,
    ROUND(
        (
            PERCENTILE_CONT(0.9)
            WITHIN GROUP (ORDER BY delivery_days)
        )::NUMERIC,
        2
    ) AS p90_delivery_days,
    COUNT(*) FILTER (
        WHERE days_after_estimate > 0
    ) AS late_orders,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE days_after_estimate > 0
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS late_order_percentage,
    ROUND(
        AVG(days_after_estimate) FILTER (
            WHERE days_after_estimate > 0
        ),
        2
    ) AS average_days_late
FROM eligible_orders
GROUP BY purchase_month
ORDER BY purchase_month;