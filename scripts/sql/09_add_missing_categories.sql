-- Preserve categories found in the products CSV
-- but missing from the translation CSV.
-- English translations remain NULL because the source
-- does not provide them.

BEGIN;

INSERT INTO public.categories (
    product_category_name,
    product_category_name_english
)
VALUES
    ('pc_gamer', NULL),
    ('portateis_cozinha_e_preparadores_de_alimentos', NULL)
ON CONFLICT (product_category_name) DO NOTHING;

COMMIT;