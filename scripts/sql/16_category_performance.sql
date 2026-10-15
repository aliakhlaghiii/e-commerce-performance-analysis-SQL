-- Category performance for delivered orders.
-- Merchandise sales exclude freight.
-- Keep products with missing categories in a separate group.
-- An order containing multiple categories is counted in each category.

WITH category_totals AS (
    SELECT
        COALESCE(
            p.product_category_name,
            'unknown'
        ) AS category_name,
        COUNT(DISTINCT o.order_id) AS delivered_orders,
        COUNT(*) AS items_sold,
        COUNT(DISTINCT oi.product_id) AS distinct_products_sold,
        SUM(oi.price) AS merchandise_sales,
        SUM(oi.freight_value) AS freight_total,
        AVG(oi.price) AS average_item_price
    FROM public.orders AS o
    INNER JOIN public.order_items AS oi
        ON oi.order_id = o.order_id
    INNER JOIN public.products AS p
        ON p.product_id = oi.product_id
    WHERE o.order_status = 'delivered'
    GROUP BY COALESCE(p.product_category_name, 'unknown')
)
SELECT
    DENSE_RANK() OVER (
        ORDER BY merchandise_sales DESC
    ) AS sales_rank,
    category_name,
    delivered_orders,
    items_sold,
    distinct_products_sold,
    ROUND(merchandise_sales, 2) AS merchandise_sales,
    ROUND(freight_total, 2) AS freight_total,
    ROUND(average_item_price, 2) AS average_item_price,
    ROUND(
        100.0 * merchandise_sales
        / NULLIF(SUM(merchandise_sales) OVER (), 0),
        2
    ) AS sales_share_percentage
FROM category_totals
ORDER BY merchandise_sales DESC, category_name;