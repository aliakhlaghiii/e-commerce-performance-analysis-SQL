import csv
import os
from pathlib import Path

import psycopg
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_COLUMNS = [
    "product_id",
    "product_category_name",
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
]


def main():
    # Load database settings and source file path.
    with (PROJECT_ROOT / "config.yaml").open(
        encoding="utf-8"
    ) as file:
        config = yaml.safe_load(file)

    db = config["database"]
    csv_path = PROJECT_ROOT / config["paths"]["products"]

    # Validate the header and count source records.
    with csv_path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.reader(file)
        header = next(reader, None)

        if header != EXPECTED_COLUMNS:
            raise ValueError(
                f"Unexpected CSV columns: {header}"
            )

        source_rows = 0

        for record_number, row in enumerate(reader, start=1):
            if len(row) != len(EXPECTED_COLUMNS):
                raise ValueError(
                    f"Invalid column count in data record "
                    f"{record_number}: {len(row)}"
                )

            source_rows += 1

    if source_rows == 0:
        raise ValueError("The source CSV contains no data.")

    # Roll back the import if loading or validation fails.
    with psycopg.connect(
        host=db["host"],
        port=db["port"],
        dbname=db["name"],
        user=os.environ["PGUSER"],
        connect_timeout=5,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM public.products;"
            )
            rows_before = cursor.fetchone()[0]

            if rows_before != 0:
                raise ValueError(
                    "products is not empty. Import stopped."
                )

            copy_sql = """
                COPY public.products (
                    product_id,
                    product_category_name,
                    product_name_lenght,
                    product_description_lenght,
                    product_photos_qty,
                    product_weight_g,
                    product_length_cm,
                    product_height_cm,
                    product_width_cm
                )
                FROM STDIN
                WITH (
                    FORMAT CSV,
                    HEADER TRUE,
                    ENCODING 'UTF8',
                    NULL '',
                    FORCE_NULL (
                        product_category_name,
                        product_name_lenght,
                        product_description_lenght,
                        product_photos_qty,
                        product_weight_g,
                        product_length_cm,
                        product_height_cm,
                        product_width_cm
                    )
                )
            """

            with csv_path.open(
                "r", encoding="utf-8-sig", newline=""
            ) as file:
                with cursor.copy(copy_sql) as copy:
                    while chunk := file.read(65536):
                        copy.write(chunk.encode("utf-8"))

            cursor.execute(
                "SELECT COUNT(*) FROM public.products;"
            )
            rows_after = cursor.fetchone()[0]
            inserted_rows = rows_after - rows_before

            if inserted_rows != source_rows:
                raise ValueError(
                    f"Row count mismatch: "
                    f"source={source_rows}, "
                    f"inserted={inserted_rows}"
                )

            # Record missing values without replacing them.
            cursor.execute("""
                SELECT
                    COUNT(*) FILTER (
                        WHERE product_category_name IS NULL
                    ),
                    COUNT(*) FILTER (
                        WHERE product_name_lenght IS NULL
                    ),
                    COUNT(*) FILTER (
                        WHERE product_description_lenght IS NULL
                    ),
                    COUNT(*) FILTER (
                        WHERE product_photos_qty IS NULL
                    ),
                    COUNT(*) FILTER (
                        WHERE product_weight_g IS NULL
                    ),
                    COUNT(*) FILTER (
                        WHERE product_length_cm IS NULL
                    ),
                    COUNT(*) FILTER (
                        WHERE product_height_cm IS NULL
                    ),
                    COUNT(*) FILTER (
                        WHERE product_width_cm IS NULL
                    )
                FROM public.products;
            """)
            missing_counts = cursor.fetchone()

    # Save the report only after the transaction commits.
    report = {
        "table_name": "products",
        "source_rows": source_rows,
        "rows_before": rows_before,
        "inserted_rows": inserted_rows,
        "rows_after": rows_after,
        "status": "PASS",
    }

    for column, count in zip(
        EXPECTED_COLUMNS[1:], missing_counts
    ):
        report[f"missing_{column}"] = count

    report_dir = PROJECT_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "products_load_report.csv"

    with report_path.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(report),
        )
        writer.writeheader()
        writer.writerow(report)

    print(f"Loaded {inserted_rows} rows into products.")

    for column, count in zip(
        EXPECTED_COLUMNS[1:], missing_counts
    ):
        print(f"Missing {column}: {count}")

    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()