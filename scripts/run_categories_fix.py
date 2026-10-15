import csv
import os
from pathlib import Path

import psycopg
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    with (PROJECT_ROOT / "config.yaml").open(
        encoding="utf-8"
    ) as file:
        config = yaml.safe_load(file)

    db = config["database"]

    sql_path = (
        PROJECT_ROOT
        / "scripts"
        / "sql"
        / "09_add_missing_categories.sql"
    )
    sql_text = sql_path.read_text(encoding="utf-8")

    # The SQL file manages its transaction with BEGIN and COMMIT.
    with psycopg.connect(
        host=db["host"],
        port=db["port"],
        dbname=db["name"],
        user=os.environ["PGUSER"],
        connect_timeout=5,
        autocommit=True,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql_text)

            # Consume the results of all statements in the file.
            while cursor.nextset():
                pass

            cursor.execute("""
                SELECT
                    product_category_name,
                    product_category_name_english
                FROM public.categories
                WHERE product_category_name IN (
                    'pc_gamer',
                    'portateis_cozinha_e_preparadores_de_alimentos'
                )
                ORDER BY product_category_name;
            """)
            categories = cursor.fetchall()

            if len(categories) != 2:
                raise ValueError(
                    "Expected both categories to exist."
                )

            cursor.execute(
                "SELECT COUNT(*) FROM public.categories;"
            )
            total_rows = cursor.fetchone()[0]

    report_dir = PROJECT_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "categories_fix_report.csv"

    with report_path.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "product_category_name",
            "product_category_name_english",
            "translation_status",
        ])

        for name, english_name in categories:
            writer.writerow([
                name,
                english_name,
                "MISSING" if english_name is None else "AVAILABLE",
            ])

    print("Both categories are present.")
    print(f"Total categories: {total_rows}")
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()