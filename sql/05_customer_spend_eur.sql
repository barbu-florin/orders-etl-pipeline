DROP TABLE IF EXISTS gold.customer_spend_eur;

CREATE TABLE gold.customer_spend_eur AS
SELECT
	o.customer_id,
	MIN(o.customer_email) AS customer_email,
	ROUND(SUM(o.amount_in_eur), 2) AS total_spend_in_eur
FROM silver.vw_orders_clean_eur AS o
WHERE o.status = 'completed'
  AND o.amount_in_eur IS NOT NULL
GROUP BY o.customer_id;
