## Data Cleaning Summary

During the inspection of `bronze.orders_raw`, several data quality issues were identified. I handled these issues during the Bronze-to-Silver transformation so that `silver.orders_clean` contains only usable records, while invalid records are stored in `silver.orders_failed` with a reason for rejection.

### Order IDs
Some order IDs required normalization due to inconsistent formatting, whitespace, or casing. I trimmed whitespace, converted IDs to uppercase, and converted empty strings to `NULL`. This ensures that equivalent order IDs are represented consistently and improves duplicate detection.

### Quantities
Some quantities were negative. Since an order quantity should represent the number of items purchased, I converted negative values to their absolute values. Missing or zero quantities are rejected because they do not represent a valid order line.

### Order timestamps
`order_ts` contained multiple formats, including ISO timestamps, European day-first dates, and Unix epoch timestamps. I created a normalization function that detects the format and converts all valid values to a PostgreSQL `TIMESTAMP`. Values that cannot be parsed are converted to `NULL` and subsequently rejected.

### Customer IDs
Some records were missing a `customer_id`, but the customer ID could be recovered from the customer's email address. For emails matching known patterns, I extracted the numeric ID and used it to fill the missing value. Existing customer IDs are preserved. Records where the customer ID could not be recovered are rejected.

### SKUs
SKU values had inconsistent formatting, such as differences in capitalization and separators. I converted them to uppercase and removed non-alphanumeric characters. When the resulting value contains eight characters, I restored the expected `XXX-XX-XXX` format. Empty or missing SKUs are rejected.

### Categories
Some records had missing categories. When a category was missing, I looked at other records with the same normalized SKU and used the most frequently occurring category. If multiple categories had the same frequency, the category value was used as a deterministic tie-breaker. If no category could be recovered, the record is rejected and moved to `silver.orders_failed`.

### Unit prices
Weird unit prices were identified. `999999` records are rejected, preventing an obviously invalid price from entering the reporting layer. A unit price of `0` is currently allowed because it can represent a legitimate free item or promotional order.

### Internal/test orders
Internal tester orders were excluded from the clean dataset. Records were identified by customer email and assigned a rejection reason because they were not considered real orders, a decision reinforced by the fact that they also had a status of `test`.

### Duplicate order lines
Duplicate records were identified using the combination of `order_id` and normalized SKU. A deterministic `ROW_NUMBER()` ranking is used to keep one record, ordering by `fx_reference_date`, `order_ts`, and `customer_email`. Additional copies are sent to `silver.orders_failed`.

### Rejected records
Rather than removing invalid data, rejected records are preserved in `silver.orders_failed` together with a `reason_of_rejection`. This provides data lineage and makes it possible to investigate the source data quality issues later.


## Production monitoring

The pipeline is run as a daily scheduled job, and the main way I monitor it in production is by checking the application logs and the row counts in the Bronze, Silver, and Gold layers after each run. The job logs the start of the ETL process, the key transformation stages, and the final completion message, and any uncaught exception is captured with a full traceback. If a daily run silently failed, I would look for the absence of the expected completion log and the missing or stale summary counts in the database.

The operational checks I am using are:

- Job lifecycle logs: ETL pipeline started, ETL pipeline completed successfully, ETL pipeline failed
- Bronze layer counts: number of rows in bronze.orders_raw and bronze.fx_rates_raw
- Silver layer counts: number of rows in silver.orders_clean, silver.orders_failed, and silver.fx_rates
- Gold layer summaries: Top 10 customers by spend and the country/category revenue breakdown above the EUR 40,000 threshold
- Any SQL execution error or Python exception, which is the clearest indicator that the job stopped before finishing

I also monitor the scheduler for missed or late runs. If a run is delayed or not present in the expected window, I inspect the ETL logs and the table counts to confirm whether the problem was a total failure, a partial run, or a data issue. A sudden drop in bronze.orders_raw or silver.orders_clean is a strong signal that the upstream source data or the cleaning rules changed unexpectedly, while an increase in silver.orders_failed indicates that more records are being rejected than normal.

## AI usage

I used **GitHub Copilot Free** and **ChatGPT** during development. GitHub Copilot Free was mainly used for inline code suggestions, boilerplate, and quick assistance with Python and SQL. ChatGPT was used to explain SQL behaviour, debug errors, compare approaches, and discuss implementation decisions.

The overall project structure and decision to use the **Medallion Architecture** were my own. I chose the Bronze/Silver/Gold separation to keep raw data, cleaning, and reporting clearly separated.

I kept AI suggestions that fit this design, including SQL functions for reusable cleaning logic, the `silver.orders_failed` table for rejected records, joins and temporary tables for the SQL transformations, and an intermediate view for the EUR conversion logic.

I adapted other suggestions to the actual dataset and requirements. For example, I customized timestamp parsing for the Unix, ISO, and day-first formats, adjusted customer ID recovery to the email patterns in the data, and used `order_id` and normalized `sku` for duplicate detection. I also chose to reject the `999999` price sentinel while allowing `0`, and identified test orders using both the email domain and `test` status.


