-- Each row represents a review record associated with an order.

CREATE TABLE public.order_reviews (
    review_id                TEXT NOT NULL,
    order_id                 TEXT NOT NULL,
    review_score             INTEGER NOT NULL,
    review_comment_title     TEXT,
    review_comment_message   TEXT,
    review_creation_date     TIMESTAMP NOT NULL,
    review_answer_timestamp  TIMESTAMP NOT NULL,

    CONSTRAINT pk_order_reviews
        PRIMARY KEY (review_id, order_id),

    CONSTRAINT fk_order_reviews_order
        FOREIGN KEY (order_id)
        REFERENCES public.orders (order_id),

    CONSTRAINT chk_review_score
        CHECK (review_score BETWEEN 1 AND 5)
);