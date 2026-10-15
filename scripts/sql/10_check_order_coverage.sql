-- Check related-record coverage by order status.
-- EXISTS avoids duplicating orders when they have
-- multiple items, payments, or reviews.

WITH order_coverage AS (
    SELECT
        o.order_id,
        o.order_status,

        EXISTS (
            SELECT 1
            FROM public.order_items AS i
            WHERE i.order_id = o.order_id
        ) AS has_items,

        EXISTS (
            SELECT 1
            FROM public.order_payments AS p
            WHERE p.order_id = o.order_id
        ) AS has_payments,

        EXISTS (
            SELECT 1
            FROM public.order_reviews AS r
            WHERE r.order_id = o.order_id
        ) AS has_reviews

    FROM public.orders AS o
)

SELECT
    order_status,
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (
        WHERE NOT has_items
    ) AS orders_without_items,
    COUNT(*) FILTER (
        WHERE NOT has_payments
    ) AS orders_without_payments,
    COUNT(*) FILTER (
        WHERE NOT has_reviews
    ) AS orders_without_reviews

FROM order_coverage
GROUP BY order_status
ORDER BY total_orders DESC, order_status;