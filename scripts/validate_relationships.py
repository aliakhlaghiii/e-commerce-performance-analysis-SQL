import pandas as pd
import yaml

from pathlib import Path


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def read_key(file_path, column):
    """Read one column and recognize blank values as missing."""
    df = pd.read_csv(
        file_path,
        usecols=[column],
        dtype="string",
    )

    return df[column].replace(r"^\s*$", pd.NA, regex=True)


def check_relationship(
    paths,
    child_table,
    child_column,
    parent_table,
    parent_column,
    nullable=False,
):
    """Check a proposed single-column foreign key relationship."""

    child = read_key(paths[child_table], child_column)
    parent = read_key(paths[parent_table], parent_column)

    parent_values = parent.dropna()

    # A foreign key must reference a unique parent key.
    parent_missing = int(parent.isna().sum())
    parent_duplicate_rows = int(
        parent_values.duplicated(keep=False).sum()
    )

    child_missing = int(child.isna().sum())

    # Missing values are counted separately from unmatched values.
    unmatched_mask = child.notna() & ~child.isin(parent_values)
    unmatched = child.loc[unmatched_mask]

    parent_valid = (
        len(parent) > 0
        and parent_missing == 0
        and parent_duplicate_rows == 0
    )

    if not parent_valid:
        result = "INVALID_PARENT_KEY"
    elif len(child) == 0:
        result = "EMPTY_CHILD"
    elif len(unmatched) > 0 or (child_missing > 0 and not nullable):
        result = "FAIL"
    else:
        result = "PASS"

    return {
        "child_table": child_table,
        "child_column": child_column,
        "parent_table": parent_table,
        "parent_column": parent_column,
        "nullable": nullable,
        "child_rows": len(child),
        "missing_child_keys": child_missing,
        "unmatched_rows": len(unmatched),
        "unmatched_unique_keys": unmatched.nunique(),
        "unmatched_examples": " | ".join(
            unmatched.drop_duplicates().head(5).tolist()
        ),
        "missing_parent_keys": parent_missing,
        "rows_in_duplicate_parent_keys": parent_duplicate_rows,
        "result": result,
    }


def main():
    config = load_config("config.yaml")
    paths = config["paths"]

    # Child table, child column, parent table, parent column, nullable
    relationships = [
        (
            "orders", "customer_id",
            "customers", "customer_id", False,
        ),
        (
            "order_items", "order_id",
            "orders", "order_id", False,
        ),
        (
            "order_items", "product_id",
            "products", "product_id", False,
        ),
        (
            "order_items", "seller_id",
            "sellers", "seller_id", False,
        ),
        (
            "order_payments", "order_id",
            "orders", "order_id", False,
        ),
        (
            "order_reviews", "order_id",
            "orders", "order_id", False,
        ),
        (
            "products", "product_category_name",
            "category_translation", "product_category_name", True,
        ),
    ]

    results = []

    for relationship in relationships:
        print(
            f"Checking: {relationship[0]}.{relationship[1]}"
            f" -> {relationship[2]}.{relationship[3]}",
            flush=True,
        )

        results.append(
            check_relationship(paths, *relationship)
        )

    report = pd.DataFrame(results)

    report_dir = Path("reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / "relationship_validation.csv"
    report.to_csv(report_path, index=False)

    print("\nResults:")
    print(
        report[
            [
                "child_table",
                "child_column",
                "parent_table",
                "missing_child_keys",
                "unmatched_rows",
                "result",
            ]
        ].to_string(index=False)
    )

    print(f"\nReport saved to: {report_path.resolve()}")


if __name__ == "__main__":
    main()