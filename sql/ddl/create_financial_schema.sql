-- DDL for Financial Data Warehouse Schema (Star Schema)

-- Dimension: Customers
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id VARCHAR(36) PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    join_date DATE
);

-- Dimension: Accounts
CREATE TABLE IF NOT EXISTS dim_accounts (
    account_id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(36) REFERENCES dim_customers(customer_id),
    account_type VARCHAR(50),
    balance NUMERIC(15, 2),
    open_date DATE,
    status VARCHAR(20)
);

-- Fact: Transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id VARCHAR(36) PRIMARY KEY,
    account_id VARCHAR(36) REFERENCES dim_accounts(account_id),
    transaction_type VARCHAR(50),
    amount NUMERIC(15, 2),
    transaction_date TIMESTAMP,
    merchant_name VARCHAR(255),
    is_fraud BOOLEAN
);

-- Staging Tables (for ELT approach)
CREATE TABLE IF NOT EXISTS stg_customers (
    customer_id VARCHAR(36),
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    country TEXT,
    join_date TEXT
);

CREATE TABLE IF NOT EXISTS stg_accounts (
    account_id VARCHAR(36),
    customer_id VARCHAR(36),
    account_type TEXT,
    balance TEXT,
    open_date TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS stg_transactions (
    transaction_id VARCHAR(36),
    account_id VARCHAR(36),
    transaction_type TEXT,
    amount TEXT,
    transaction_date TEXT,
    merchant_name TEXT,
    is_fraud TEXT
);
