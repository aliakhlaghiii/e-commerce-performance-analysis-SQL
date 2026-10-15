-- Inspect missing payments, zero-value payments,
-- and nonpositive installment counts.
-- Aggregate items first to avoid multiplying their values.

WITH item_totals AS (
    SELECT
        order_id,
        COUNT(*) AS item_count,
        SUM(price) AS item_value,
        SUM(freight_value) AS freight_value
    FROM public.order_items
    GROUP BY order_id
),

payment_totals AS (
    SELECT
        order_id,
        COUNT(*) AS payment_record_count,
        SUM(payment_value) AS order_payment_total
    FROM public.order_payments
    GROUP BY order_id
),

anomalies AS (
    SELECT
        'missing_payment' AS issue_type,
        o.order_id,
        NULL::INTEGER AS payment_sequential,
        NULL::TEXT AS payment_type,
        NULL::INTEGER AS payment_installments,
        NULL::NUMERIC AS payment_value
    FROM public.orders AS o
    WHERE NOT EXISTS (
        SELECT 1
        FROM public.order_payments AS p
        WHERE p.order_id = o.order_id
    )

    UNION ALL

    SELECT
        'zero_payment_value',
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value
    FROM public.order_payments
    WHERE payment_value = 0

    UNION ALL

    SELECT
        'nonpositive_installments',
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value
    FROM public.order_payments
    WHERE payment_installments <= 0
)

SELECT
    a.issue_type,
    a.order_id,
    o.order_status,
    o.order_purchase_timestamp,
    a.payment_sequential,
    a.payment_type,
    a.payment_installments,
    a.payment_value,
    COALESCE(i.item_count, 0) AS item_count,
    i.item_value,
    i.freight_value,
    i.item_value + i.freight_value AS item_and_freight_total,
    COALESCE(p.payment_record_count, 0) AS payment_record_count,
    p.order_payment_total

FROM anomalies AS a
JOIN public.orders AS o
    ON o.order_id = a.order_id
LEFT JOIN item_totals AS i
    ON i.order_id = a.order_id
LEFT JOIN payment_totals AS p
    ON p.order_id = a.order_id

ORDER BY
    a.issue_type,
    a.order_id,
    a.payment_sequential;