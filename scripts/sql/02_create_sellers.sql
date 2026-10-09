-- Each row represents one seller.

CREATE TABLE public.sellers (
    seller_id                 TEXT PRIMARY KEY,
    seller_zip_code_prefix    VARCHAR(5) NOT NULL,
    seller_city               TEXT NOT NULL,
    seller_state              VARCHAR(2) NOT NULL
);