-- Monthly merchandise sales and average order value.
-- Include only delivered orders, grouped by purchase month.
-- Merchandise sales and AOV exclude freight.
-- Aggregate items before joining to avoid double counting.

WITH item_totals AS (
    SELECT
        order_id,
        COUNT(*) AS item_count,
        SUM(price) AS merchandise_value,
        SUM(freight_value) AS freight_value
    FROM public.order_items
    GROUP BY order_id
),
monthly_sales AS (
    SELECT
        DATE_TRUNC(
            'month', o.order_purchase_timestamp
        )::DATE AS purchase_month,
        COUNT(*) AS delivered_orders,
        SUM(i.item_count) AS items_sold,
        SUM(i.merchandise_value) AS merchandise_sales,
        SUM(i.freight_value) AS freight_total,
        SUM(i.merchandise_value)
            / NULLIF(COUNT(*), 0) AS average_order_value
    FROM public.orders AS o
    INNER JOIN item_totals AS i
        ON i.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY
        DATE_TRUNC('month', o.order_purchase_timestamp)::DATE
)
SELECT
    purchase_month,
    delivered_orders,
    items_sold,
    ROUND(merchandise_sales, 2) AS merchandise_sales,
    ROUND(freight_total, 2) AS freight_total,
    ROUND(
        merchandise_sales + freight_total, 2
    ) AS merchandise_and_freight_total,
    ROUND(average_order_value, 2) AS average_order_value
FROM monthly_sales
ORDER BY purchase_month;