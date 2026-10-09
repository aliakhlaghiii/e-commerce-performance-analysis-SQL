-- Each row represents one product.
-- Column names match the original CSV, including "lenght".

CREATE TABLE public.products (
    product_id                  TEXT PRIMARY KEY,
    product_category_name       TEXT,
    product_name_lenght         INTEGER,
    product_description_lenght  INTEGER,
    product_photos_qty          INTEGER,
    product_weight_g            INTEGER,
    product_length_cm           INTEGER,
    product_height_cm           INTEGER,
    product_width_cm            INTEGER,

    CONSTRAINT fk_products_category
        FOREIGN KEY (product_category_name)
        REFERENCES public.categories (product_category_name)
);