-- Summarize missing and inconsistent timestamps by order status.
-- Checks can overlap; do not add their counts together.

SELECT
    order_status,
    COUNT(*) AS total_orders,

    COUNT(*) FILTER (
        WHERE order_approved_at IS NULL
    ) AS missing_approval_date,

    COUNT(*) FILTER (
        WHERE order_delivered_carrier_date IS NULL
    ) AS missing_carrier_date,

    COUNT(*) FILTER (
        WHERE order_delivered_customer_date IS NULL
    ) AS missing_delivery_date,

    COUNT(*) FILTER (
        WHERE order_approved_at < order_purchase_timestamp
    ) AS approval_before_purchase,

    COUNT(*) FILTER (
        WHERE order_delivered_carrier_date
              < order_purchase_timestamp
    ) AS carrier_before_purchase,

    COUNT(*) FILTER (
        WHERE order_delivered_customer_date
              < order_purchase_timestamp
    ) AS delivery_before_purchase,

    COUNT(*) FILTER (
        WHERE order_delivered_carrier_date
              < order_approved_at
    ) AS carrier_before_approval,

    COUNT(*) FILTER (
        WHERE order_delivered_customer_date
              < order_delivered_carrier_date
    ) AS delivery_before_carrier,

    COUNT(*) FILTER (
        WHERE order_estimated_delivery_date::DATE
              < order_purchase_timestamp::DATE
    ) AS estimated_date_before_purchase,

    COUNT(*) FILTER (
        WHERE order_status <> 'delivered'
          AND order_delivered_customer_date IS NOT NULL
    ) AS non_delivered_with_delivery_date

FROM public.orders
GROUP BY order_status
ORDER BY total_orders DESC, order_status;