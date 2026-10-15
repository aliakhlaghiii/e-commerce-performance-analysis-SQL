-- Define eligibility for purchase-to-delivery analysis.
-- Compare calendar dates for lateness because the estimated
-- delivery timestamp represents a promised delivery date.

WITH eligible_orders AS (
    SELECT
        order_id,
        order_purchase_timestamp,
        order_delivered_customer_date,
        order_estimated_delivery_date

    FROM public.orders

    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
      AND order_delivered_customer_date
          >= order_purchase_timestamp
)

SELECT
    (
        SELECT COUNT(*)
        FROM public.orders
        WHERE order_status = 'delivered'
    ) AS total_delivered_orders,

    COUNT(*) AS eligible_orders,

    (
        SELECT COUNT(*)
        FROM public.orders
        WHERE order_status = 'delivered'
    ) - COUNT(*) AS excluded_orders,

    ROUND(
        AVG(
            EXTRACT(
                EPOCH FROM (
                    order_delivered_customer_date
                    - order_purchase_timestamp
                )
            ) / 86400.0
        ),
        2
    ) AS average_delivery_days,

    COUNT(*) FILTER (
        WHERE order_delivered_customer_date::DATE
              > order_estimated_delivery_date::DATE
    ) AS late_orders,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE order_delivered_customer_date::DATE
                  > order_estimated_delivery_date::DATE
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS late_order_percentage

FROM eligible_orders;