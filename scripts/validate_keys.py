import pandas as pd
import yaml

from pathlib import Path


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def check_key(df, dataset_name, columns, purpose):
    """Check whether a single or composite key is unique and complete."""

    # Treat empty and whitespace-only key values as missing.
    # The original dataframe is not modified.
    key_data = df[columns].replace(r"^\s*$", pd.NA, regex=True)

    missing_mask = key_data.isna().any(axis=1)
    complete_keys = key_data.loc[~missing_mask]

    # Count every row participating in a repeated complete key.
    duplicate_mask = complete_keys.duplicated(keep=False)

    # Count distinct key combinations that occur more than once.
    duplicate_groups = (
        complete_keys.loc[duplicate_mask]
        .drop_duplicates()
        .shape[0]
    )

    missing_rows = int(missing_mask.sum())
    duplicate_rows = int(duplicate_mask.sum())

    # An empty dataset cannot confirm that a key is suitable.
    if len(df) == 0:
        result = "EMPTY"
    elif missing_rows == 0 and duplicate_rows == 0:
        result = "PASS"
    else:
        result = "FAIL"

    return {
        "dataset": dataset_name,
        "key_columns": " + ".join(columns),
        "purpose": purpose,
        "rows": len(df),
        "rows_with_missing_key": missing_rows,
        "rows_in_duplicate_keys": duplicate_rows,
        "duplicate_key_groups": duplicate_groups,
        "result": result,
    }


def main():
    config = load_config("config.yaml")
    paths = config["paths"]

    # Each tuple contains: key columns and reason for checking.
    checks = {
        "customers": [
            (["customer_id"], "Primary key candidate"),
            (["customer_unique_id"], "Customer repetition check"),
        ],
        "orders": [
            (["order_id"], "Primary key candidate"),
            (["customer_id"], "Customer-to-order cardinality check"),
        ],
        "products": [
            (["product_id"], "Primary key candidate"),
        ],
        "sellers": [
            (["seller_id"], "Primary key candidate"),
        ],
        "order_items": [
            (
                ["order_id", "order_item_id"],
                "Composite primary key candidate",
            ),
        ],
        "order_payments": [
            (
                ["order_id", "payment_sequential"],
                "Composite primary key candidate",
            ),
        ],
        "category_translation": [
            (["product_category_name"], "Primary key candidate"),
        ],
        "order_reviews": [
            (["review_id"], "Primary key candidate"),
            (
                ["review_id", "order_id"],
                "Composite primary key candidate",
            ),
            (["order_id"], "Reviews-per-order check"),
        ],
        "geolocation": [
            (
                ["geolocation_zip_code_prefix"],
                "Postal-prefix uniqueness check",
            ),
        ],
    }

    results = []

    for dataset_name, dataset_checks in checks.items():
        # Read only the columns required for these checks.
        required_columns = sorted({
            column
            for columns, purpose in dataset_checks
            for column in columns
        })

        print(f"Checking: {dataset_name}", flush=True)

        df = pd.read_csv(
            paths[dataset_name],
            dtype="string",
            usecols=required_columns,
        )

        for columns, purpose in dataset_checks:
            result = check_key(
                df,
                dataset_name,
                columns,
                purpose,
            )
            results.append(result)

        # Keep only one dataset in memory at a time.
        del df

    report = pd.DataFrame(results)

    report_dir = Path("reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / "key_validation.csv"
    report.to_csv(report_path, index=False)

    print("\nKey validation results:")
    print(report.to_string(index=False))
    print(f"\nReport saved to: {report_path.resolve()}")


if __name__ == "__main__":
    main()