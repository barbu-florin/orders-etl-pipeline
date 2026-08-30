DROP TABLE IF EXISTS gold.country_category_breakdown;

CREATE TABLE gold.country_category_breakdown AS
WITH per_country AS (
	SELECT
		o.country,
		ROUND(SUM(o.amount_in_eur), 2) AS revenue_in_eur
	FROM silver.vw_orders_clean_eur AS o
	WHERE o.status = 'completed'
	  AND o.category IN ('Books', 'Electronics')
	  AND o.amount_in_eur IS NOT NULL
	GROUP BY o.country
)
SELECT
	country,
	revenue_in_eur
FROM per_country
WHERE revenue_in_eur > 40000
ORDER BY revenue_in_eur DESC;
