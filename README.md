# E-Commerce Performance Analysis with SQL & Python

A PostgreSQL and Python project for loading, validating, and analyzing the Olist e-commerce dataset. It covers relational modeling, data quality checks, sales analysis, repeat purchasing, and delivery performance.

**Stack:** PostgreSQL · Python 3.12 · psycopg · SQL · DBeaver · GitHub Actions

## Analysis Report

Results, interpretations, metric definitions, and analytical limitations are documented separately in the [analysis report](reports/analysis_summary.md).

## Project Scope

- Profile CSV files and validate keys and relationships.
- Create relational tables with primary keys, composite keys, and foreign keys.
- Load data using Python and PostgreSQL `COPY FROM STDIN`.
- Investigate missing records, payment differences, and inconsistent dates.
- Analyze monthly sales and AOV, category performance, repeat purchasing, and delivery times.
- Export SQL results to reproducible CSV reports.
- Run static Python checks through GitHub Actions.

PostgreSQL performs the analysis. Python handles ingestion, validation, and report execution. DBeaver is used to inspect tables and query results.

## Technical Design

### Data model

The database contains `customers`, `orders`, `sellers`, `categories`, `products`, `order_items`, `order_payments`, `order_reviews`, and `geolocation`.

- Orders reference customers; items reference orders, products, and sellers.
- Products reference categories; payments and reviews reference orders.
- Composite keys support multiple items and payments per order.
- Reviews use `(review_id, order_id)` because `review_id` alone is not unique in the source.
- Geolocation uses a generated identifier. ZIP prefixes are not unique and must be aggregated appropriately before geographic joins.
- Monetary values use fixed-precision numeric types.

### Python ingestion

- Project-relative paths with `pathlib` and configuration with YAML.
- BOM-aware CSV reading with `utf-8-sig`.
- Header and row-count validation.
- Bulk loading through psycopg and PostgreSQL COPY.
- Transactional imports and nonempty-table guards.
- Per-table CSV load reports.

The loaders are intended for initial imports. They stop when their target table already contains data; they are not incremental upsert pipelines.

### SQL analysis

The queries use CTEs, `EXISTS`, conditional aggregation, window functions, date arithmetic, and ordered-set aggregates such as `PERCENTILE_CONT`.

Items and payments are aggregated separately to order level before reconciliation. This prevents one-to-many joins from multiplying monetary totals. Customer analysis uses `customer_unique_id` to identify repeat purchasers across orders.

The reusable `run_sql_report.py` script executes one result-producing SQL statement in a read-only session, exports all rows to CSV, and prints the first 20 rows.

## Repository Structure

```text
.
├── .github/workflows/ci.yml
├── config.yaml
├── requirements.txt
├── data/                         # Source CSV files supplied locally
├── scripts/
│   ├── profile_raw_data.py
│   ├── validate_keys.py
│   ├── validate_relationships.py
│   ├── test_db_connection.py
│   ├── load_*.py                 # Table-specific loading scripts
│   ├── run_categories_fix.py
│   ├── run_sql_report.py
│   └── sql/                      # Schema, checks, and analyses
└── reports/
    ├── *.csv
    └── analysis_summary.md
```

## Setup

### 1. Install dependencies

Prerequisites: Python 3.12, PostgreSQL, and optionally DBeaver for database inspection and schema execution.

```bash
git clone https://github.com/aliakhlaghiii/e-commerce-performance-analysis-SQL.git
cd e-commerce-performance-analysis-SQL

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Required runtime dependencies are `pandas`, `PyYAML`, and `psycopg[binary]`.

### 2. Obtain the data

Download the [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and place the following files in `data/`:

```text
olist_customers_dataset.csv
olist_geolocation_dataset.csv
olist_order_items_dataset.csv
olist_order_payments_dataset.csv
olist_order_reviews_dataset.csv
olist_orders_dataset.csv
olist_products_dataset.csv
olist_sellers_dataset.csv
product_category_name_translation.csv
```

### 3. Configure the database

Create a PostgreSQL database named `olist`. Review the connection settings and CSV paths in `config.yaml`. Analytical SQL uses the `public` schema.

Set your PostgreSQL role and test connectivity:

```bash
export PGUSER=your_postgres_username
python3 scripts/test_db_connection.py
```

Configure authentication for your PostgreSQL installation. Keep credentials out of version control.

### 4. Create the schema

Connect DBeaver to `olist` and execute schema scripts numbered **01 through 08**, in order, from `scripts/sql/`.

### 5. Load the data

Run these commands from the repository root, in dependency order:

```bash
python3 scripts/load_categories.py
python3 scripts/run_categories_fix.py
python3 scripts/load_customers.py
python3 scripts/load_orders.py
python3 scripts/load_sellers.py
python3 scripts/load_products.py
python3 scripts/load_order_items.py
python3 scripts/load_order_payments.py
python3 scripts/load_order_reviews.py
python3 scripts/load_geolocation.py
```

The category fix runs before product loading to supply missing category keys. Review the generated load reports before running the analyses. Successful loading does not mean the source is free of quality issues.

## Running Queries

Use the same runner for quality checks and business analyses:

```bash
python3 scripts/run_sql_report.py \
  scripts/sql/10_check_order_coverage.sql \
  reports/order_coverage_report.csv

python3 scripts/run_sql_report.py \
  scripts/sql/15_monthly_sales.sql \
  reports/monthly_sales_report.csv

python3 scripts/run_sql_report.py \
  scripts/sql/19_project_kpi_summary.sql \
  reports/project_kpi_summary.csv
```

SQL files can also be run directly in DBeaver. The Python runner provides the CSV export workflow without requiring `psql`.

### Query index

SQL files are under `scripts/sql/`; CSV outputs are under `reports/`.

| SQL file | Output |
|---|---|
| `10_check_order_coverage.sql` | `order_coverage_report.csv` |
| `11_check_payment_anomalies.sql` | `payment_anomalies_report.csv` |
| `12_check_order_dates.sql` | `order_dates_report.csv` |
| `13_check_delivery_eligibility.sql` | `delivery_eligibility_report.csv` |
| `14_check_payment_reconciliation.sql` | `payment_reconciliation_report.csv` |
| `15_monthly_sales.sql` | `monthly_sales_report.csv` |
| `16_category_performance.sql` | `category_performance_report.csv` |
| `17_repeat_customers.sql` | `repeat_customers_report.csv` |
| `18_delivery_performance.sql` | `delivery_performance_report.csv` |
| `19_project_kpi_summary.sql` | `project_kpi_summary.csv` |

## Continuous Integration

The [GitHub Actions workflow](.github/workflows/ci.yml) runs on pushes and pull requests and supports manual execution with `workflow_dispatch`.

Using Python 3.12, it checks:

- Python syntax under `scripts/` using `compileall`.
- Selected critical Python errors using Ruff rules `E9,F63,F7,F82`.

Run the same checks locally:

```bash
python3 -m pip install ruff==0.11.13
python3 -m compileall -q scripts
python3 -m ruff check scripts --select E9,F63,F7,F82
```

Execution logs are available in the repository's **Actions** tab. These are static checks: they do not execute loaders, connect to PostgreSQL, validate analytical results, or build and deploy a package.

## Future Improvements

- PostgreSQL integration tests with small fixtures and known expected results.
- Tests for loader rollback, BOM handling, and repeated-import protection.
- SQL linting and downloadable CI test reports.

## Data Attribution

Source: [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). Refer to the dataset page for its usage terms.

## Author

[Ali Akhlaghi](https://github.com/aliakhlaghiii)
