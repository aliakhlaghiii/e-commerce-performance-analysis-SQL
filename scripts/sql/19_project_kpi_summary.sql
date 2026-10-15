-- Project KPI summary.
-- Sales and customer metrics use delivered orders.
-- Merchandise sales and AOV exclude freight.
-- Delivery metrics use valid purchase-to-delivery endpoints.
-- Repeat customers have at least two delivered orders
-- within the observed dataset.

WITH item_totals AS (
    SELECT
        order_id,
        COUNT(*) AS item_count,
        SUM(price) AS merchandise_value,
        SUM(freight_value) AS freight_value
    FROM public.order_items
    GROUP BY order_id
),
delivered_orders AS (
    SELECT
        o.order_id,
        c.customer_unique_id,
        o.order_purchase_timestamp,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,
        i.item_count,
        i.merchandise_value,
        i.freight_value
    FROM public.orders AS o
    INNER JOIN public.customers AS c
        ON c.customer_id = o.customer_id
    LEFT JOIN item_totals AS i
        ON i.order_id = o.order_id
    WHERE o.order_status = 'delivered'
),
sales_summary AS (
    SELECT
        MIN(order_purchase_timestamp)::DATE AS first_purchase_date,
        MAX(order_purchase_timestamp)::DATE AS last_purchase_date,
        COUNT(*) AS delivered_orders,
        SUM(item_count) AS items_sold,
        SUM(merchandise_value) AS merchandise_sales,
        SUM(freight_value) AS freight_total,
        SUM(merchandise_value)
            / NULLIF(COUNT(*), 0) AS average_order_value
    FROM delivered_orders
),
customer_totals AS (
    SELECT
        customer_unique_id,
        COUNT(*) AS order_count
    FROM delivered_orders
    GROUP BY customer_unique_id
),
customer_summary AS (
    SELECT
        COUNT(*) AS unique_customers,
        COUNT(*) FILTER (
            WHERE order_count >= 2
        ) AS repeat_customers,
        100.0 * COUNT(*) FILTER (
            WHERE order_count >= 2
        ) / NULLIF(COUNT(*), 0) AS repeat_customer_percentage
    FROM customer_totals
),
delivery_summary AS (
    SELECT
        COUNT(*) AS delivery_eligible_orders,
        AVG(
            EXTRACT(
                EPOCH FROM (
                    order_delivered_customer_date
                    - order_purchase_timestamp
                )
            ) / 86400.0
        ) AS average_delivery_days,
        COUNT(*) FILTER (
            WHERE order_delivered_customer_date::DATE
                > order_estimated_delivery_date::DATE
        ) AS late_orders,
        100.0 * COUNT(*) FILTER (
            WHERE order_delivered_customer_date::DATE
                > order_estimated_delivery_date::DATE
        ) / NULLIF(COUNT(*), 0) AS late_order_percentage
    FROM delivered_orders
    WHERE order_delivered_customer_date IS NOT NULL
      AND order_delivered_customer_date >= order_purchase_timestamp
)
SELECT
    (SELECT COUNT(*) FROM public.orders) AS total_orders_all_statuses,
    s.first_purchase_date,
    s.last_purchase_date,
    s.delivered_orders,
    s.items_sold,
    ROUND(s.merchandise_sales, 2) AS merchandise_sales,
    ROUND(s.freight_total, 2) AS freight_total,
    ROUND(s.average_order_value, 2) AS average_order_value,
    c.unique_customers,
    c.repeat_customers,
    ROUND(
        c.repeat_customer_percentage, 2
    ) AS repeat_customer_percentage,
    d.delivery_eligible_orders,
    s.delivered_orders
        - d.delivery_eligible_orders AS delivery_excluded_orders,
    ROUND(d.average_delivery_days, 2) AS average_delivery_days,
    d.late_orders,
    ROUND(d.late_order_percentage, 2) AS late_order_percentage
FROM sales_summary AS s
CROSS JOIN customer_summary AS c
CROSS JOIN delivery_summary AS d;