-- Compare payments with item prices plus freight at order level.
-- Aggregate each detail table before joining to avoid double counting.
-- Keep missing records separate from monetary differences.

WITH item_totals AS (
    SELECT
        order_id,
        SUM(price + freight_value) AS expected_total
    FROM public.order_items
    GROUP BY order_id
),
payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS payment_total
    FROM public.order_payments
    GROUP BY order_id
),
classified_orders AS (
    SELECT
        o.order_id,
        o.order_status,
        i.expected_total,
        p.payment_total,
        p.payment_total - i.expected_total AS difference,
        CASE
            WHEN i.order_id IS NULL AND p.order_id IS NULL
                THEN 'missing_items_and_payments'
            WHEN i.order_id IS NULL
                THEN 'missing_items'
            WHEN p.order_id IS NULL
                THEN 'missing_payments'
            WHEN ABS(p.payment_total - i.expected_total) <= 0.01
                THEN 'matched_within_tolerance'
            WHEN p.payment_total > i.expected_total
                THEN 'payment_above_items_and_freight'
            ELSE 'payment_below_items_and_freight'
        END AS reconciliation_status
    FROM public.orders AS o
    LEFT JOIN item_totals AS i
        ON i.order_id = o.order_id
    LEFT JOIN payment_totals AS p
        ON p.order_id = o.order_id
)
SELECT
    order_status,
    reconciliation_status,
    COUNT(*) AS order_count,
    ROUND(SUM(expected_total), 2) AS total_items_and_freight,
    ROUND(SUM(payment_total), 2) AS total_payments,
    ROUND(SUM(difference), 2) AS net_difference,
    ROUND(SUM(ABS(difference)), 2) AS total_absolute_difference
FROM classified_orders
GROUP BY order_status, reconciliation_status
ORDER BY order_status, reconciliation_status;