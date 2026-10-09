-- Multiple location records may share the same ZIP code prefix.
-- The generated ID identifies each stored row.

CREATE TABLE public.geolocation (
    geolocation_id               BIGINT GENERATED ALWAYS AS IDENTITY
                                 PRIMARY KEY,
    geolocation_zip_code_prefix  VARCHAR(5) NOT NULL,
    geolocation_lat              DOUBLE PRECISION NOT NULL,
    geolocation_lng              DOUBLE PRECISION NOT NULL,
    geolocation_city             TEXT NOT NULL,
    geolocation_state            VARCHAR(2) NOT NULL
);