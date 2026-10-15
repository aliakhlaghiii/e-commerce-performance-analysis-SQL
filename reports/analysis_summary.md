# E-Commerce Performance Analysis — Results and Interpretation

## Executive Summary

The dataset contains 99,441 orders across all statuses. Analysis of the 96,478 delivered orders shows BRL 13.22 million in merchandise sales and an average order value of BRL 137.04. Repeat purchasers account for 3.00% of customers with delivered orders and 5.51% of merchandise sales.

Among orders with valid delivery endpoints, average delivery time is 12.56 days and 6.77% arrive after the estimated date. Monthly results show substantial variation in delivery performance, with March 2018 standing out for late deliveries.

These findings describe the observed historical dataset. They do not establish profitability, long-term retention, or the causes of delivery delays.

## Scope and Definitions

Sales and customer analyses include only orders whose recorded status is `delivered`. Their purchase dates range from **September 15, 2016 to August 29, 2018**. Monthly results are grouped by purchase month, not delivery month.

| Metric | Definition |
|---|---|
| Merchandise sales | Sum of item prices, excluding freight |
| Average order value (AOV) | Merchandise sales divided by delivered orders |
| Customer | Distinct `customer_unique_id` |
| Repeat customer | Customer with at least two delivered orders in the observed dataset |
| Delivery duration | Elapsed purchase-to-delivery time in days |
| Late delivery | Actual delivery calendar date after the estimated calendar date |
| Late delivery percentage | Late orders divided by orders eligible for delivery analysis |

Merchandise sales are not payment receipts, profit, or net accounting revenue. All monetary amounts below are in BRL.

## Overall Performance

| Metric | Result |
|---|---:|
| Orders across all statuses | 99,441 |
| Delivered orders | 96,478 |
| Items in delivered orders | 110,197 |
| Merchandise sales | 13,221,498.11 |
| Freight value | 2,198,275.64 |
| AOV, excluding freight | 137.04 |
| Unique customers with delivered orders | 93,358 |
| Repeat customers | 2,801 |
| Repeat customer percentage | 3.00% |
| Orders eligible for delivery analysis | 96,470 |
| Orders excluded from delivery analysis | 8 |
| Average delivery duration | 12.56 days |
| Late deliveries | 6,534 |
| Late delivery percentage | 6.77% |

Source: [Project KPI summary](project_kpi_summary.csv).

## 1. Monthly Sales and Order Value

**November 2017 was the highest-sales month in the observed data**, with merchandise sales of **987,765.37** and **7,289 delivered orders**. Its AOV was **135.51**.

| Purchase month | Delivered orders | Merchandise sales | AOV |
|---|---:|---:|---:|
| October 2017 | 4,478 | 648,247.65 | 144.76 |
| November 2017 | 7,289 | 987,765.37 | 135.51 |
| December 2017 | 5,513 | 726,033.19 | 131.69 |

### Interpretation

The November peak coincides with a higher number of orders, while AOV is lower than in October. Order volume and order value therefore tell different parts of the sales story. The output alone does not identify the role of promotions, seasonality, or changes in the product mix.

Early observations are sparse: September and December 2016 each contain only one delivered order. November 2016 has no row in this delivered-order report. These observations should not be treated as a stable baseline for growth comparisons.

Source: [Monthly sales report](monthly_sales_report.csv).

## 2. Product Category Performance

| Category | Merchandise sales | Sales share | Delivered orders containing the category |
|---|---:|---:|---:|
| Beauty and health (`beleza_saude`) | 1,233,131.72 | 9.33% | 8,647 |
| Watches and gifts (`relogios_presentes`) | 1,166,176.98 | 8.82% | 5,495 |
| Bed, table, and bath (`cama_mesa_banho`) | 1,023,434.76 | 7.74% | 9,272 |

The top three categories account for approximately **25.89%** of merchandise sales, based on rounded category shares.

### Interpretation

Beauty and health leads by sales, while bed, table, and bath has more orders among these three categories. Watches and gifts generates a higher sales total than bed, table, and bath despite fewer orders; its average item price is also higher (**199.04 versus 93.44**).

This supports reviewing category performance using both value and volume. It does not show which category is most profitable, because cost and margin data are not included.

Products with missing categories remain under `unknown`. Category order counts must not be summed to obtain overall orders: a single order can contain several categories. Average item price is distinct from AOV.

Source: [Category performance report](category_performance_report.csv).

## 3. Repeat Purchasing

| Segment | Customers | Customer share | Delivered orders | Sales share | Orders per customer | AOV |
|---|---:|---:|---:|---:|---:|---:|
| One-time | 90,557 | 97.00% | 90,557 | 94.49% | 1.00 | 137.96 |
| Repeat | 2,801 | 3.00% | 5,921 | 5.51% | 2.11 | 123.02 |

### Interpretation

Repeat purchasers contribute a larger share of sales than their share of customers. Their observed contribution comes through multiple purchases, while their average order value is lower than that of one-time purchasers.

The 3.00% figure is an observed repeat-purchase percentage, not a monthly retention rate or a measure of lifetime loyalty. Customers entering near the end of the dataset have less time to place a second order. A fairer retention comparison would use acquisition cohorts with equal follow-up windows.

Source: [Repeat customer report](repeat_customers_report.csv).

## 4. Delivery Performance

Across **96,470 eligible orders**, delivery takes **12.56 days** on average. **6,534 orders (6.77%)** arrive after the estimated calendar date.

| Purchase month | Eligible orders | Average delivery days | P90 delivery days | Late delivery percentage |
|---|---:|---:|---:|---:|
| November 2017 | 7,288 | 15.16 | 27.21 | 12.40% |
| February 2018 | 6,555 | 16.95 | 31.02 | 14.13% |
| March 2018 | 7,003 | 16.30 | 32.19 | 18.96% |
| June 2018 | 6,096 | 9.24 | 15.91 | 1.16% |
| August 2018 | 6,351 | 7.73 | 13.07 | 6.19% |

P90 is the estimated duration at or below which approximately 90% of eligible orders were delivered.

### Interpretation

March 2018 has the highest late delivery percentage among purchase months in 2017–2018, with **1,328 late orders**. Its P90 duration of **32.19 days** indicates that the slower end of delivery performance is substantially worse than the mean alone suggests.

November 2017 combines peak sales with an elevated late delivery percentage. This is a useful period for investigation, but the association does not prove that order volume caused delays.

Average delivery time falls between March and August 2018. However, faster delivery and lower lateness are different measures: August has a shorter average duration than June but a higher late delivery percentage. Lateness also depends on the promised date.

End-of-dataset coverage and the delivered-only filter limit conclusions about improvement in the final months. September 2016's 100% late rate represents just one order and should not be generalized.

Sources: [Delivery eligibility](delivery_eligibility_report.csv) and [monthly delivery performance](delivery_performance_report.csv).

## 5. Data Quality Findings and Their Impact

### Order coverage

Across all statuses, **775 orders have no items**, **one has no payment record**, and **768 have no review**. Of the orders without items, 767 are canceled or unavailable. Their status helps contextualize missing records but does not establish the underlying cause.

All delivered orders have items. The single delivered order without a payment record remains in merchandise sales because its item prices are available; the missing payment is not treated as zero.

Source: [Order coverage report](order_coverage_report.csv).

### Payments

The anomaly report identifies **nine zero-value payment records** and **two zero-installment payment records**, in addition to the order missing a payment. A zero payment record does not necessarily mean the entire order was unpaid: some orders contain multiple payment records.

Among delivered orders:

| Reconciliation outcome | Orders |
|---|---:|
| Matched within BRL 0.01 per order | 96,178 |
| Payments above item prices plus freight | 260 |
| Payments below item prices plus freight | 39 |
| Missing payment records | 1 |

For the 299 orders outside tolerance, the excess totals **3,031.22** and the shortfall totals **199.08**, giving a net difference of **2,832.14**. This net value excludes the small within-tolerance differences.

The reconciliation identifies differences, not their causes. Source amounts remain unchanged, and item-based sales are kept distinct from payments.

Sources: [Payment anomalies](payment_anomalies_report.csv) and [payment reconciliation](payment_reconciliation_report.csv).

### Dates

Eight delivered orders lack customer-delivery timestamps. They remain in sales metrics but are excluded from delivery metrics.

Among delivered orders, 165 have carrier timestamps before purchase, 1,350 have carrier timestamps before approval, and 23 have customer-delivery timestamps before carrier timestamps. These flags may overlap and must not be added to estimate distinct affected orders.

Purchase-to-delivery calculations use valid purchase and delivery endpoints; inconsistent intermediate timestamps do not automatically invalidate that duration. Six canceled orders have customer-delivery timestamps but remain excluded from delivered-order analysis.

Source: [Order date quality report](order_dates_report.csv).

## Limitations

- Results describe historical records, not current market conditions.
- Sales and customer findings are conditional on recorded delivered status.
- Sparse initial months and the observation cutoff limit time comparisons.
- The monthly queries omit months with no qualifying orders.
- Repeat purchasing uses unequal customer observation periods.
- Missing data and timestamp inconsistencies affect which metrics can be calculated.
- Costs and refund adjustments are not modeled; profit and net accounting revenue cannot be inferred.
- Associations in these reports do not establish causal effects.

## Business Follow-up

1. Investigate February–March 2018 delays by seller, destination, and handoff timing, with date-quality filters appropriate to each metric.
2. Review capacity and inventory for high-sales categories using cost and margin data before prioritizing commercial investment.
3. Measure repeat purchasing by acquisition cohort with equal follow-up periods.
4. Investigate payment discrepancies before substituting payment totals for item-based sales.

These are proposed investigations, not actions whose effectiveness has been tested in this project.
