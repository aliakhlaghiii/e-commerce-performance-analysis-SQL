-- Repeat purchasing among customers with delivered orders.
-- Identify customers using customer_unique_id.
-- A repeat customer has at least two delivered orders
-- within the observed dataset.
-- Merchandise sales exclude freight.

WITH item_totals AS (
    SELECT
        order_id,
        SUM(price) AS merchandise_value
    FROM public.order_items
    GROUP BY order_id
),
customer_totals AS (
    SELECT
        c.customer_unique_id,
        COUNT(*) AS delivered_orders,
        SUM(i.merchandise_value) AS merchandise_sales
    FROM public.orders AS o
    INNER JOIN public.customers AS c
        ON c.customer_id = o.customer_id
    INNER JOIN item_totals AS i
        ON i.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
customer_segments AS (
    SELECT
        CASE
            WHEN delivered_orders = 1 THEN 'one_time'
            ELSE 'repeat'
        END AS customer_segment,
        COUNT(*) AS customer_count,
        SUM(delivered_orders) AS delivered_orders,
        SUM(merchandise_sales) AS merchandise_sales
    FROM customer_totals
    GROUP BY
        CASE
            WHEN delivered_orders = 1 THEN 'one_time'
            ELSE 'repeat'
        END
)
SELECT
    customer_segment,
    customer_count,
    ROUND(
        100.0 * customer_count
        / NULLIF(SUM(customer_count) OVER (), 0),
        2
    ) AS customer_share_percentage,
    delivered_orders,
    ROUND(merchandise_sales, 2) AS merchandise_sales,
    ROUND(
        100.0 * merchandise_sales
        / NULLIF(SUM(merchandise_sales) OVER (), 0),
        2
    ) AS sales_share_percentage,
    ROUND(
        delivered_orders::NUMERIC / NULLIF(customer_count, 0),
        2
    ) AS average_orders_per_customer,
    ROUND(
        merchandise_sales / NULLIF(delivered_orders, 0),
        2
    ) AS average_order_value
FROM customer_segments
ORDER BY customer_segment;