import csv
import os
from pathlib import Path

import psycopg
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_COLUMNS = [
    "order_id",
    "order_item_id",
    "product_id",
    "seller_id",
    "shipping_limit_date",
    "price",
    "freight_value",
]


def main():
    # Load database settings and source file path.
    with (PROJECT_ROOT / "config.yaml").open(
        encoding="utf-8"
    ) as file:
        config = yaml.safe_load(file)

    db = config["database"]
    csv_path = PROJECT_ROOT / config["paths"]["order_items"]

    # Validate the header and count source records.
    # utf-8-sig removes a BOM if present.
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

    # Commit only if loading and validation both succeed.
    with psycopg.connect(
        host=db["host"],
        port=db["port"],
        dbname=db["name"],
        user=os.environ["PGUSER"],
        connect_timeout=5,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM public.order_items;"
            )
            rows_before = cursor.fetchone()[0]

            # Prevent accidentally importing the same data twice.
            if rows_before != 0:
                raise ValueError(
                    "order_items is not empty. Import stopped."
                )

            copy_sql = """
                COPY public.order_items (
                    order_id,
                    order_item_id,
                    product_id,
                    seller_id,
                    shipping_limit_date,
                    price,
                    freight_value
                )
                FROM STDIN
                WITH (
                    FORMAT CSV,
                    HEADER TRUE,
                    ENCODING 'UTF8'
                )
            """

            # Stream the CSV into PostgreSQL.
            with csv_path.open(
                "r", encoding="utf-8-sig", newline=""
            ) as file:
                with cursor.copy(copy_sql) as copy:
                    while chunk := file.read(65536):
                        copy.write(chunk.encode("utf-8"))

            cursor.execute(
                "SELECT COUNT(*) FROM public.order_items;"
            )
            rows_after = cursor.fetchone()[0]
            inserted_rows = rows_after - rows_before

            if inserted_rows != source_rows:
                raise ValueError(
                    f"Row count mismatch: "
                    f"source={source_rows}, "
                    f"inserted={inserted_rows}"
                )

            # Summarize all imported items, regardless of order status.
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT order_id),
                    SUM(price),
                    SUM(freight_value),
                    COUNT(*) FILTER (WHERE price < 0),
                    COUNT(*) FILTER (WHERE freight_value < 0)
                FROM public.order_items;
            """)

            (
                distinct_orders,
                total_item_price,
                total_freight_value,
                negative_price_rows,
                negative_freight_rows,
            ) = cursor.fetchone()

    # Write the report after the transaction commits.
    # PASS refers to successful loading and matching row counts.
    report = {
        "table_name": "order_items",
        "source_rows": source_rows,
        "rows_before": rows_before,
        "inserted_rows": inserted_rows,
        "rows_after": rows_after,
        "distinct_orders": distinct_orders,
        "total_item_price": total_item_price,
        "total_freight_value": total_freight_value,
        "negative_price_rows": negative_price_rows,
        "negative_freight_rows": negative_freight_rows,
        "status": "PASS",
    }

    report_dir = PROJECT_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "order_items_load_report.csv"

    with report_path.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(report),
        )
        writer.writeheader()
        writer.writerow(report)

    print(f"Loaded {inserted_rows} rows into order_items.")
    print(f"Distinct orders: {distinct_orders}")
    print(f"Total item price: {total_item_price}")
    print(f"Total freight value: {total_freight_value}")
    print(f"Negative price rows: {negative_price_rows}")
    print(f"Negative freight rows: {negative_freight_rows}")
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()