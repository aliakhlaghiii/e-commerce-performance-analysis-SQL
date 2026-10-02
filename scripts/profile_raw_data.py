import pandas as pd
import yaml
from pathlib import Path
from contextlib import redirect_stdout

def load_config(config_path):
    """Load settings from a YAML file."""
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_data(file_path):
    """Read a CSV while preserving IDs and leading zeros."""
    return pd.read_csv(file_path, dtype="string")


def check_dataframe(df, name):
    """Print an initial overview without modifying the data."""
    print(f"\n{'=' * 60}")
    print(f"Dataset: {name}")
    print(f"Rows: {df.shape[0]:,}")
    print(f"Columns: {df.shape[1]}")
    print(f"Fully duplicated rows: {df.duplicated().sum():,}")

    print("\nFirst 5 rows:")
    print(df.head().to_string(index=False))

    # Identify missing values and whitespace-only fields.
    missing = df.isna() | df.apply(
        lambda column: column.str.strip().eq("").fillna(False)
    )

    summary = pd.DataFrame({
        "column": df.columns,
        "missing_count": missing.sum().to_numpy(),
        "missing_percent": (
            missing.mean().mul(100).round(2).to_numpy()
        ),
    })

    print("\nMissing values:")
    print(summary.to_string(index=False))


def main():
    config = load_config("config.yaml")
    paths = config["paths"]

    # Read each dataset separately using its configured path.
    customers = load_data(paths["customers"])
    geolocation = load_data(paths["geolocation"])
    order_items = load_data(paths["order_items"])
    order_payments = load_data(paths["order_payments"])
    order_reviews = load_data(paths["order_reviews"])
    orders = load_data(paths["orders"])
    products = load_data(paths["products"])
    sellers = load_data(paths["sellers"])
    category_translation = load_data(paths["category_translation"])

    datasets = {
        "customers": customers,
        "geolocation": geolocation,
        "order_items": order_items,
        "order_payments": order_payments,
        "order_reviews": order_reviews,
        "orders": orders,
        "products": products,
        "sellers": sellers,
        "category_translation": category_translation,
    }

    for name, df in datasets.items():
        check_dataframe(df, name)


if __name__ == "__main__":
    report_dir = Path("reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / "initial_data_profile.txt"

    with report_path.open("w", encoding="utf-8") as file:
        with redirect_stdout(file):
            main()

    print(f"Report saved to: {report_path.resolve()}")