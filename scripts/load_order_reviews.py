import csv
import os
from pathlib import Path

import psycopg
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_COLUMNS = [
    "review_id",
    "order_id",
    "review_score",
    "review_comment_title",
    "review_comment_message",
    "review_creation_date",
    "review_answer_timestamp",
]


def main():
    # Load database settings and source file path.
    with (PROJECT_ROOT / "config.yaml").open(
        encoding="utf-8"
    ) as file:
        config = yaml.safe_load(file)

    db = config["database"]
    csv_path = PROJECT_ROOT / config["paths"]["order_reviews"]

    # Count CSV records correctly, including multiline comments.
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
                "SELECT COUNT(*) FROM public.order_reviews;"
            )
            rows_before = cursor.fetchone()[0]

            if rows_before != 0:
                raise ValueError(
                    "order_reviews is not empty. Import stopped."
                )

            copy_sql = """
                COPY public.order_reviews (
                    review_id,
                    order_id,
                    review_score,
                    review_comment_title,
                    review_comment_message,
                    review_creation_date,
                    review_answer_timestamp
                )
                FROM STDIN
                WITH (
                    FORMAT CSV,
                    HEADER TRUE,
                    ENCODING 'UTF8',
                    NULL '',
                    FORCE_NULL (
                        review_comment_title,
                        review_comment_message
                    )
                )
            """

            # Preserve comment text, quotes, and embedded newlines.
            with csv_path.open(
                "r", encoding="utf-8-sig", newline=""
            ) as file:
                with cursor.copy(copy_sql) as copy:
                    while chunk := file.read(65536):
                        copy.write(chunk.encode("utf-8"))

            cursor.execute(
                "SELECT COUNT(*) FROM public.order_reviews;"
            )
            rows_after = cursor.fetchone()[0]
            inserted_rows = rows_after - rows_before

            if inserted_rows != source_rows:
                raise ValueError(
                    f"Row count mismatch: "
                    f"source={source_rows}, "
                    f"inserted={inserted_rows}"
                )

            cursor.execute("""
                SELECT
                    COUNT(DISTINCT order_id),
                    COUNT(*) FILTER (
                        WHERE review_comment_title IS NULL
                    ),
                    COUNT(*) FILTER (
                        WHERE review_comment_message IS NULL
                    ),
                    MIN(review_score),
                    MAX(review_score)
                FROM public.order_reviews;
            """)

            (
                distinct_orders,
                missing_titles,
                missing_messages,
                minimum_score,
                maximum_score,
            ) = cursor.fetchone()

    # Write the report after the transaction commits.
    report = {
        "table_name": "order_reviews",
        "source_rows": source_rows,
        "rows_before": rows_before,
        "inserted_rows": inserted_rows,
        "rows_after": rows_after,
        "distinct_orders": distinct_orders,
        "missing_comment_titles": missing_titles,
        "missing_comment_messages": missing_messages,
        "minimum_review_score": minimum_score,
        "maximum_review_score": maximum_score,
        "status": "PASS",
    }

    report_dir = PROJECT_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "order_reviews_load_report.csv"

    with report_path.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(report),
        )
        writer.writeheader()
        writer.writerow(report)

    print(f"Loaded {inserted_rows} rows into order_reviews.")
    print(f"Distinct orders: {distinct_orders}")
    print(f"Missing comment titles: {missing_titles}")
    print(f"Missing comment messages: {missing_messages}")
    print(f"Review score range: {minimum_score} to {maximum_score}")
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()