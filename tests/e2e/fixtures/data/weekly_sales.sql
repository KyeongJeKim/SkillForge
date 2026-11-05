-- Weekly sales by channel (last full week)
SELECT
    d.week_start_date,
    o.channel_name,
    COUNT(DISTINCT o.order_id)  AS order_cnt,
    SUM(o.net_sales_amt)        AS net_sales_amt,
    SUM(o.net_sales_amt) / NULLIF(COUNT(DISTINCT o.order_id), 0) AS aov
FROM analytics.fct_orders o
JOIN analytics.dim_date d ON o.order_date = d.date_key
WHERE d.week_start_date = DATEADD(week, -1, DATE_TRUNC('week', CURRENT_DATE))
GROUP BY 1, 2
ORDER BY net_sales_amt DESC;
