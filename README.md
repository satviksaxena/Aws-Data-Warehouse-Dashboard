# AWS Financial Data Warehouse & Executive Dashboard

This repository contains a complete, production-ready ETL pipeline and interactive dashboard for processing, storing, and visualizing financial transaction data. Built entirely on AWS Cloud Infrastructure, it simulates a modern cloud data architecture using industry best practices.

## Project Architecture & Business Value

Financial institutions need to track transaction volumes, active accounts, and detect fraudulent behavior efficiently. This project provides a scalable solution to handle these requirements by:

1. **Ingesting raw data** and storing it in a data lake (AWS S3).
2. **Transforming and Loading (ELT)** data into a well-structured Data Warehouse using an optimized Star Schema and Redshift's Massively Parallel Processing (MPP) `COPY` commands.
3. **Orchestrating** the entire workflow automatically on a daily schedule using Apache Airflow.
4. **Visualizing** key performance indicators (KPIs) through a real-time, premium dashboard built with Streamlit connected directly to the Data Warehouse.

### Technical Stack
* **Orchestration:** Apache Airflow (Dockerized)
* **Data Warehouse:** AWS Redshift Serverless
* **Storage:** AWS S3 (Data Lake)
* **Data Transformation:** Python, SQL (ELT approach)
* **Visualization:** Streamlit, Plotly
* **Infrastructure:** Docker & Docker Compose

## The Need for the Project

As financial institutions rapidly expand their digital footprints, they generate millions of transaction records daily. Legacy systems often struggle to query this massive scale of data quickly enough to provide actionable insights. 
This project was built to solve this problem by migrating local, siloed data into a **Cloud-Native Data Warehouse**. By leveraging AWS Redshift's Massively Parallel Processing (MPP) and an ELT (Extract, Load, Transform) architecture, the business can now identify fraudulent transactions, track active users, and monitor total volume in near real-time, empowering executives to make data-driven decisions.

## The Data Architecture & Schema

The data is modeled using a Kimball **Star Schema** optimized for analytical read-heavy workloads (OLAP).

### 1. Fact Table: `fact_transactions`
Contains the core quantitative metrics and foreign keys to dimensions.
* `transaction_id` (PK, VARCHAR)
* `account_id` (FK, VARCHAR)
* `transaction_type` (VARCHAR - e.g., Deposit, Withdrawal, Transfer)
* `amount` (NUMERIC)
* `transaction_date` (TIMESTAMP)
* `merchant_name` (VARCHAR)
* `is_fraud` (BOOLEAN)

### 2. Dimension Tables
* **`dim_customers`**: `customer_id`, `first_name`, `last_name`, `email`, `city`, `country`, `join_date`.
* **`dim_accounts`**: `account_id`, `customer_id` (FK), `account_type`, `balance`, `open_date`, `status` (Active/Inactive).

## Major SQL Queries Used

The Streamlit dashboard executes complex analytical queries directly against AWS Redshift to generate insights:

* **Customer Segmentation (CTEs & Aggregations):** 
  Uses Common Table Expressions (CTEs) to join facts and dimensions, aggregating total transactions and balances to categorize users into cohorts (e.g., *High Value - Active*, *Standard User*).
* **Fraud Rate Analysis (Conditional Aggregation):** 
  Utilizes `SUM(CASE WHEN is_fraud = TRUE THEN 1 ELSE 0 END)` divided by the total transaction count to calculate fraud percentages dynamically per merchant.
* **Time-Series Analysis (Date Truncation):** 
  Groups transaction sums by `DATE(transaction_date)` over rolling 30-day windows to plot volume trends over time.

## Repository Structure

* **`dags/`**: Contains the Airflow DAG (`financial_etl_dag.py`) that manages the pipeline execution.
* **`sql/`**: Table creation scripts (`create_financial_schema.sql`) defining the Star Schema (Fact and Dimension tables).
* **`dashboard/`**: Streamlit application (`app.py`) for the executive dashboard.
* **`scripts/`**: Python scripts for generating mock financial data (`data_generation/`) and interacting with AWS S3 (`aws/`).
* **`docker-compose.yml`**: Infrastructure setup for Airflow and Streamlit containers.

## How to Run & Setup

### 1. Configure Environment Variables
You must provide your own AWS credentials and Redshift endpoint. Create a file named `.env` in the root directory and add the following variables:

```env
# AWS Credentials
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET_NAME=your-s3-bucket-name

# AWS Redshift Credentials
DB_HOST=your-workgroup-name.123456789.us-east-1.redshift-serverless.amazonaws.com
DB_PORT=5439
DB_NAME=dev
DB_USER=admin
DB_PASSWORD=your_redshift_password
AWS_REDSHIFT_IAM_ROLE=arn:aws:iam::123456789:role/your-redshift-role
```

### 2. Verify AWS Connection
Before spinning up the infrastructure, verify your local machine can connect to AWS S3 and Redshift:
```bash
python3 test_aws_connection.py
```
*(Ensure that "Publicly accessible" is enabled in your Redshift Serverless Workgroup network settings).*

### 3. Start the Infrastructure
Ensure Docker Desktop is running, then execute:
```bash
docker-compose up -d
```

### 4. Run the Pipeline
1. Access the **Airflow Web UI** at `http://localhost:8081` (Username: `airflow`, Password: `airflow`).
2. Unpause and trigger the `financial_etl_pipeline` DAG.
3. The DAG will automatically generate data, upload to S3, build the Redshift schema, run the `COPY` commands, and execute the ELT transformations.

### 5. View the Dashboard
Access the **Streamlit Dashboard** at `http://localhost:8501`.

---

## Dashboard Previews

*(Add screenshots of the Streamlit dashboard here)*

![Executive Dashboard Overview](./path-to-screenshot1.png)
![Advanced Analytics & Fraud Breakdowns](./path-to-screenshot2.png)
