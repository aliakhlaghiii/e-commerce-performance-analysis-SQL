-- Each row represents one payment record for an order.

CREATE TABLE public.order_payments (
    order_id              TEXT NOT NULL,
    payment_sequential    INTEGER NOT NULL,
    payment_type          TEXT NOT NULL,
    payment_installments  INTEGER NOT NULL,
    payment_value         NUMERIC(12, 2) NOT NULL,

    CONSTRAINT pk_order_payments
        PRIMARY KEY (order_id, payment_sequential),

    CONSTRAINT fk_order_payments_order
        FOREIGN KEY (order_id)
        REFERENCES public.orders (order_id)
);