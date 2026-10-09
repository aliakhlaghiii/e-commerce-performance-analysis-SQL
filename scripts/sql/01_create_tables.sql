-- Create customers and orders in the olist database.

BEGIN;

CREATE TABLE public.customers (
    customer_id                 TEXT PRIMARY KEY,
    customer_unique_id          TEXT NOT NULL,
    customer_zip_code_prefix    VARCHAR(5) NOT NULL,
    customer_city               TEXT NOT NULL,
    customer_state              VARCHAR(2) NOT NULL
);

CREATE TABLE public.orders (
    order_id                        TEXT PRIMARY KEY,
    customer_id                     TEXT NOT NULL,
    order_status                    TEXT NOT NULL,
    order_purchase_timestamp        TIMESTAMP NOT NULL,
    order_approved_at               TIMESTAMP,
    order_delivered_carrier_date    TIMESTAMP,
    order_delivered_customer_date   TIMESTAMP,
    order_estimated_delivery_date   TIMESTAMP NOT NULL,

    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES public.customers (customer_id)
);

COMMIT;