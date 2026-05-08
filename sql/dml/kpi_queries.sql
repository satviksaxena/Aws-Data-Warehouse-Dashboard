-- Complex SQL Queries for KPI Reporting

-- 1. Monthly Transaction Volume and Month-over-Month Growth
WITH MonthlyStats AS (
    SELECT 
        DATE_TRUNC('month', transaction_date) AS txn_month,
        SUM(amount) AS total_volume,
        COUNT(transaction_id) AS txn_count
    FROM fact_transactions
    GROUP BY DATE_TRUNC('month', transaction_date)
)
SELECT 
    txn_month,
    total_volume,
    txn_count,
    LAG(total_volume) OVER (ORDER BY txn_month) AS prev_month_volume,
    CASE 
        WHEN LAG(total_volume) OVER (ORDER BY txn_month) > 0 
        THEN ((total_volume - LAG(total_volume) OVER (ORDER BY txn_month)) / LAG(total_volume) OVER (ORDER BY txn_month)) * 100 
        ELSE 0 
    END AS mom_growth_percentage
FROM MonthlyStats
ORDER BY txn_month DESC;


-- 2. Customer Segmentation by Transaction Activity and Account Balance
WITH CustomerActivity AS (
    SELECT 
        c.customer_id,
        c.first_name,
        c.last_name,
        SUM(a.balance) AS total_balance,
        COUNT(t.transaction_id) AS total_transactions,
        SUM(t.amount) AS total_spent
    FROM dim_customers c
    JOIN dim_accounts a ON c.customer_id = a.customer_id
    LEFT JOIN fact_transactions t ON a.account_id = t.account_id
    GROUP BY c.customer_id, c.first_name, c.last_name
)
SELECT 
    customer_id,
    first_name,
    last_name,
    total_balance,
    total_transactions,
    total_spent,
    CASE 
        WHEN total_balance > 50000 AND total_transactions > 50 THEN 'High Value - Active'
        WHEN total_balance > 50000 THEN 'High Value - Inactive'
        WHEN total_transactions > 50 THEN 'Active User'
        ELSE 'Standard User'
    END AS customer_segment
FROM CustomerActivity
ORDER BY total_balance DESC;


-- 3. Fraud Detection Analysis by Merchant
SELECT 
    merchant_name,
    COUNT(transaction_id) AS total_transactions,
    SUM(CASE WHEN is_fraud = TRUE THEN 1 ELSE 0 END) AS fraud_transactions,
    SUM(amount) AS total_revenue,
    SUM(CASE WHEN is_fraud = TRUE THEN amount ELSE 0 END) AS fraud_amount,
    (SUM(CASE WHEN is_fraud = TRUE THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(transaction_id), 0)) AS fraud_rate_percentage
FROM fact_transactions
GROUP BY merchant_name
HAVING COUNT(transaction_id) > 10
ORDER BY fraud_rate_percentage DESC
LIMIT 20;


-- 4. Top Accounts with Highest Velocity of Transactions (Potential Money Laundering / High Frequency Trading)
SELECT 
    a.account_id,
    c.first_name,
    c.last_name,
    a.account_type,
    COUNT(t.transaction_id) AS txn_count_last_30_days,
    SUM(t.amount) AS total_amount_last_30_days
FROM dim_accounts a
JOIN dim_customers c ON a.customer_id = c.customer_id
JOIN fact_transactions t ON a.account_id = t.account_id
WHERE t.transaction_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY a.account_id, c.first_name, c.last_name, a.account_type
HAVING COUNT(t.transaction_id) > 100
ORDER BY txn_count_last_30_days DESC;
