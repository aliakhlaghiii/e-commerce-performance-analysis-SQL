import csv
import os
from pathlib import Path

import psycopg
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_COLUMNS = [
    "order_id",
    "customer_id",
    "order_status",
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]


def main():
    # Load database settings and source file path.
    with (PROJECT_ROOT / "config.yaml").open(
        encoding="utf-8"
    ) as file:
        config = yaml.safe_load(file)

    db = config["database"]
    csv_path = PROJECT_ROOT / config["paths"]["orders"]

    # Validate the header and count CSV records.
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
                "SELECT COUNT(*) FROM public.orders;"
            )
            rows_before = cursor.fetchone()[0]

            if rows_before != 0:
                raise ValueError(
                    "orders is not empty. Import stopped."
                )

            copy_sql = """
                COPY public.orders (
                    order_id,
                    customer_id,
                    order_status,
                    order_purchase_timestamp,
                    order_approved_at,
                    order_delivered_carrier_date,
                    order_delivered_customer_date,
                    order_estimated_delivery_date
                )
                FROM STDIN
                WITH (
                    FORMAT CSV,
                    HEADER TRUE,
                    ENCODING 'UTF8',
                    NULL '',
                    FORCE_NULL (
                        order_approved_at,
                        order_delivered_carrier_date,
                        order_delivered_customer_date
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
                "SELECT COUNT(*) FROM public.orders;"
            )
            rows_after = cursor.fetchone()[0]
            inserted_rows = rows_after - rows_before

            if inserted_rows != source_rows:
                raise ValueError(
                    f"Row count mismatch: "
                    f"source={source_rows}, "
                    f"inserted={inserted_rows}"
                )

            # Count missing optional timestamps for the report.
            cursor.execute("""
                SELECT
                    COUNT(*) FILTER (
                        WHERE order_approved_at IS NULL
                    ),
                    COUNT(*) FILTER (
                        WHERE order_delivered_carrier_date IS NULL
                    ),
                    COUNT(*) FILTER (
                        WHERE order_delivered_customer_date IS NULL
                    )
                FROM public.orders;
            """)

            (
                missing_approved_at,
                missing_carrier_date,
                missing_customer_date,
            ) = cursor.fetchone()

    # Write the report after the database commit succeeds.
    report_dir = PROJECT_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "orders_load_report.csv"

    report = {
        "table_name": "orders",
        "source_rows": source_rows,
        "rows_before": rows_before,
        "inserted_rows": inserted_rows,
        "rows_after": rows_after,
        "missing_approved_at": missing_approved_at,
        "missing_carrier_date": missing_carrier_date,
        "missing_customer_date": missing_customer_date,
        "status": "PASS",
    }

    with report_path.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(report),
        )
        writer.writeheader()
        writer.writerow(report)

    print(f"Loaded {inserted_rows} rows into orders.")
    print(f"Missing approval timestamps: {missing_approved_at}")
    print(f"Missing carrier timestamps: {missing_carrier_date}")
    print(f"Missing delivery timestamps: {missing_customer_date}")
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()