"""Generate charts from the project's SQL report CSV files."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, PercentFormatter
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"

BLUE = "#2563EB"
TEAL = "#0F766E"
ORANGE = "#EA580C"
GRAY = "#64748B"

# Focus monthly charts on 2017–2018.
# The original CSV reports retain the sparse 2016 observations.
CHART_START = pd.Timestamp("2017-01-01")

CATEGORY_LABELS = {
    "beleza_saude": "Beauty & health",
    "relogios_presentes": "Watches & gifts",
    "cama_mesa_banho": "Bed, table & bath",
    "esporte_lazer": "Sports & leisure",
    "informatica_acessorios": "Computers & accessories",
    "moveis_decoracao": "Furniture & decor",
    "utilidades_domesticas": "Housewares",
    "cool_stuff": "Cool stuff",
    "automotivo": "Automotive",
    "brinquedos": "Toys",
    "unknown": "Unknown category",
}


def read_report(filename, required_columns):
    """Read a report and verify the columns used by the charts."""
    path = REPORTS / filename

    if not path.is_file():
        raise FileNotFoundError(f"Required report not found: {path}")

    frame = pd.read_csv(path, encoding="utf-8-sig")

    missing = set(required_columns) - set(frame.columns)
    if missing:
        raise ValueError(
            f"{filename}: missing columns: {sorted(missing)}"
        )

    if frame.empty:
        raise ValueError(f"{filename}: report is empty.")

    return frame


def numeric_columns(frame, columns):
    """Reject invalid numeric text rather than silently dropping it."""
    frame = frame.copy()

    for column in columns:
        frame[column] = pd.to_numeric(frame[column], errors="raise")

    return frame


def monthly_frame(frame):
    """Add absent months as NaN so lines do not imply zero sales."""
    frame = frame.copy()
    frame["purchase_month"] = pd.to_datetime(
        frame["purchase_month"], errors="raise"
    )

    if frame["purchase_month"].isna().any():
        raise ValueError("Missing purchase month.")

    if frame["purchase_month"].duplicated().any():
        raise ValueError("Expected one row per purchase month.")

    frame = (
        frame.set_index("purchase_month")
        .sort_index()
        .loc[CHART_START:]
    )

    if frame.empty:
        raise ValueError("No monthly observations from January 2017.")

    months = pd.date_range(
        frame.index.min(),
        frame.index.max(),
        freq="MS",
    )

    return frame.reindex(months)


def style_axis(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=0.2)


def format_months(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.set_xlabel("Purchase month")


def save_chart(fig, filename, note):
    fig.text(
        0.02,
        0.025,
        note,
        fontsize=9,
        color=GRAY,
        va="bottom",
    )
    fig.tight_layout(rect=(0, 0.11, 1, 0.93))

    path = FIGURES / filename
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")


def plot_monthly_sales():
    columns = [
        "purchase_month",
        "delivered_orders",
        "merchandise_sales",
    ]
    frame = read_report("monthly_sales_report.csv", columns)
    frame = numeric_columns(frame, columns[1:])
    frame = monthly_frame(frame)

    fig, axes = plt.subplots(
        2, 1, figsize=(12, 8), sharex=True
    )
    fig.suptitle(
        "Monthly merchandise sales and order volume",
        fontsize=17,
        fontweight="bold",
    )

    axes[0].plot(
        frame.index,
        frame["merchandise_sales"] / 1_000_000,
        color=BLUE,
        marker="o",
        markersize=4,
        linewidth=2,
    )
    axes[0].set_ylabel("Merchandise sales (BRL millions)")
    axes[0].set_ylim(bottom=0)

    axes[1].plot(
        frame.index,
        frame["delivered_orders"],
        color=TEAL,
        marker="o",
        markersize=4,
        linewidth=2,
    )
    axes[1].set_ylabel("Delivered orders")
    axes[1].set_ylim(bottom=0)
    axes[1].yaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{value:,.0f}")
    )

    peak_month = frame["merchandise_sales"].idxmax()
    peak_value = frame.loc[peak_month, "merchandise_sales"]

    axes[0].annotate(
        f"Peak: {peak_month:%b %Y}\nBRL {peak_value:,.0f}",
        xy=(peak_month, peak_value / 1_000_000),
        xytext=(-85, -50),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->", "color": GRAY},
        fontsize=9,
    )

    for ax in axes:
        style_axis(ax)

    format_months(axes[1])

    save_chart(
        fig,
        "monthly_sales.png",
        "Source: monthly_sales_report.csv | Delivered orders; freight excluded.\n"
        "2017 onward shown; sparse 2016 observations omitted. Missing months "
        "remain gaps. Final cohorts may be affected by the data cutoff.",
    )


def plot_top_categories():
    columns = [
        "category_name",
        "merchandise_sales",
        "sales_share_percentage",
    ]
    frame = read_report("category_performance_report.csv", columns)
    frame = numeric_columns(frame, columns[1:])

    top = (
        frame.nlargest(10, "merchandise_sales")
        .sort_values("merchandise_sales")
        .copy()
    )

    labels = (
        top["category_name"]
        .map(CATEGORY_LABELS)
        .fillna(top["category_name"])
    )

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.suptitle(
        "Top 10 product categories by merchandise sales",
        fontsize=17,
        fontweight="bold",
    )

    values = top["merchandise_sales"].to_numpy() / 1_000_000
    shares = top["sales_share_percentage"].to_numpy()
    positions = list(range(len(top)))

    ax.barh(positions, values, color=BLUE, height=0.65)
    ax.set_yticks(positions)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Merchandise sales (BRL millions)")
    ax.set_xlim(0, max(values) * 1.28)

    for position, value, share in zip(positions, values, shares):
        ax.text(
            value + max(values) * 0.015,
            position,
            f"{value:.2f}m | {share:.2f}%",
            va="center",
            fontsize=9,
        )

    style_axis(ax)
    ax.grid(False)
    ax.grid(axis="x", alpha=0.2)

    save_chart(
        fig,
        "top_categories.png",
        "Source: category_performance_report.csv | Delivered orders; freight excluded.\n"
        "Percentages are shares of sales across all categories, not only the top 10.",
    )


def plot_repeat_customers():
    columns = [
        "customer_segment",
        "customer_share_percentage",
        "sales_share_percentage",
    ]
    frame = read_report("repeat_customers_report.csv", columns)
    frame = numeric_columns(frame, columns[1:])

    expected = {"one_time", "repeat"}
    if (
        frame["customer_segment"].duplicated().any()
        or set(frame["customer_segment"]) != expected
    ):
        raise ValueError(
            "Expected exactly one 'one_time' and one 'repeat' segment."
        )

    frame = frame.set_index("customer_segment").loc[
        ["one_time", "repeat"]
    ]

    fig, ax = plt.subplots(figsize=(10, 7))
    fig.suptitle(
        "Customer share versus merchandise sales share",
        fontsize=17,
        fontweight="bold",
    )

    positions = [0, 1]
    width = 0.34

    customer_bars = ax.bar(
        [position - width / 2 for position in positions],
        frame["customer_share_percentage"],
        width=width,
        label="Share of customers",
        color=BLUE,
    )
    sales_bars = ax.bar(
        [position + width / 2 for position in positions],
        frame["sales_share_percentage"],
        width=width,
        label="Share of merchandise sales",
        color=TEAL,
    )

    for bars in (customer_bars, sales_bars):
        ax.bar_label(
            bars,
            labels=[f"{bar.get_height():.2f}%" for bar in bars],
            padding=4,
            fontsize=10,
        )

    ax.set_xticks(positions)
    ax.set_xticklabels(["One-time customers", "Repeat customers"])
    ax.set_ylabel("Share")
    ax.set_ylim(0, 110)
    ax.set_yticks(range(0, 101, 20))
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=100))
    ax.legend(loc="upper right")
    style_axis(ax)

    save_chart(
        fig,
        "repeat_customers.png",
        "Source: repeat_customers_report.csv | Customers identified by customer_unique_id.\n"
        "Repeat = at least two delivered orders in the observed period. "
        "This is not a cohort retention rate.",
    )


def plot_delivery_performance():
    columns = [
        "purchase_month",
        "eligible_orders",
        "average_delivery_days",
        "p90_delivery_days",
        "late_orders",
        "late_order_percentage",
    ]
    raw = read_report("delivery_performance_report.csv", columns)
    raw = numeric_columns(raw, columns[1:])

    eligible_total = raw["eligible_orders"].sum()
    if eligible_total <= 0:
        raise ValueError("Delivery report has no eligible orders.")

    # Use order counts, not the average of monthly percentages.
    overall_late_rate = (
        100 * raw["late_orders"].sum() / eligible_total
    )

    frame = monthly_frame(raw)

    fig, axes = plt.subplots(
        2, 1, figsize=(12, 9), sharex=True
    )
    fig.suptitle(
        "Monthly delivery duration and lateness",
        fontsize=17,
        fontweight="bold",
    )

    axes[0].plot(
        frame.index,
        frame["average_delivery_days"],
        label="Average delivery time",
        color=BLUE,
        marker="o",
        markersize=4,
        linewidth=2,
    )
    axes[0].plot(
        frame.index,
        frame["p90_delivery_days"],
        label="90th percentile",
        color=TEAL,
        linestyle="--",
        linewidth=2,
    )
    axes[0].set_ylabel("Purchase-to-delivery days")
    axes[0].set_ylim(bottom=0)
    axes[0].legend(loc="upper right")

    axes[1].bar(
        frame.index,
        frame["late_order_percentage"],
        width=20,
        color=ORANGE,
        alpha=0.85,
        label="Monthly late delivery rate",
    )
    axes[1].axhline(
        overall_late_rate,
        color=GRAY,
        linestyle="--",
        linewidth=1.5,
        label=f"Full-period rate: {overall_late_rate:.2f}%",
    )
    axes[1].set_ylabel("Late delivery percentage")
    axes[1].yaxis.set_major_formatter(PercentFormatter(xmax=100))
    axes[1].set_ylim(
        0,
        max(
            frame["late_order_percentage"].max(),
            overall_late_rate,
        ) * 1.35,
    )
    axes[1].legend(loc="upper left", fontsize=9)

    peak_month = frame["late_order_percentage"].idxmax()
    peak_rate = frame.loc[peak_month, "late_order_percentage"]
    peak_count = int(frame.loc[peak_month, "eligible_orders"])

    axes[1].annotate(
        f"{peak_month:%b %Y}: {peak_rate:.2f}%\n"
        f"{peak_count:,} eligible orders",
        xy=(peak_month, peak_rate),
        xytext=(12, 12),
        textcoords="offset points",
        fontsize=9,
    )

    for ax in axes:
        style_axis(ax)

    format_months(axes[1])

    save_chart(
        fig,
        "delivery_performance.png",
        "Source: delivery_performance_report.csv | Valid delivered orders; grouped by purchase month.\n"
        "Late = delivered after the estimated calendar date. "
        "Charts show 2017 onward; reference rate includes all months.\n"
        "Sparse 2016 observations omitted from charts. "
        "Final cohorts may be affected by the data cutoff.",
    )


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.labelsize": 11,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )

    plot_monthly_sales()
    plot_top_categories()
    plot_repeat_customers()
    plot_delivery_performance()

    print("Created 4 charts successfully.")


if __name__ == "__main__":
    main()