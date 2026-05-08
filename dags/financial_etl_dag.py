import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
import logging

# We will add /opt/airflow to path if needed, but relative imports might fail
import sys
sys.path.append('/opt/airflow')

from scripts.data_generation.generate_financial_data import main as generate_data
from utils.aws_s3 import S3Manager

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'financial_etl_pipeline',
    default_args=default_args,
    description='ETL pipeline for financial data warehouse',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['finance', 'etl', 'aws'],
)

def task_generate_data():
    logging.info("Starting data generation...")
    generate_data()

def task_upload_to_s3():
    bucket = os.getenv('AWS_S3_BUCKET_NAME')
    if not bucket or not os.getenv('AWS_ACCESS_KEY_ID'):
        logging.warning("AWS credentials or bucket name not found. Skipping S3 upload.")
        return
        
    s3 = S3Manager()
    landing_dir = '/opt/airflow/data/landing'
    
    for file in os.listdir(landing_dir):
        if file.endswith('.csv'):
            file_path = os.path.join(landing_dir, file)
            s3.upload_file(file_path, bucket, f"landing/{file}")

def task_load_staging():
    bucket = os.getenv('AWS_S3_BUCKET_NAME')
    iam_role = os.getenv('AWS_REDSHIFT_IAM_ROLE')
    
    if bucket and iam_role:
        logging.info("AWS Credentials found. Using Redshift COPY command for MPP Data Loading.")
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "datawarehouse"),
            user=os.getenv("DB_USER", "airflow"),
            password=os.getenv("DB_PASSWORD", "airflow")
        )
        cur = conn.cursor()
        
        tables = {
            'customers.csv': 'stg_customers',
            'accounts.csv': 'stg_accounts',
            'transactions.csv': 'stg_transactions'
        }
        
        for file, table in tables.items():
            s3_path = f"s3://{bucket}/landing/{file}"
            copy_query = f"""
                COPY {table}
                FROM '{s3_path}'
                IAM_ROLE '{iam_role}'
                CSV IGNOREHEADER 1;
            """
            logging.info(f"Executing COPY command for {table}")
            cur.execute(copy_query)
        
        conn.commit()
        cur.close()
        conn.close()
    else:
        logging.warning("Missing AWS S3 Bucket or IAM Role. Falling back to local pandas load for mocked environment.")
        hook = PostgresHook(postgres_conn_id='datawarehouse_conn') 
        engine = hook.get_sqlalchemy_engine()
        landing_dir = '/opt/airflow/data/landing'
        
        files_to_tables = {
            'customers.csv': 'stg_customers',
            'accounts.csv': 'stg_accounts',
            'transactions.csv': 'stg_transactions'
        }
        
        for file, table in files_to_tables.items():
            file_path = os.path.join(landing_dir, file)
            if os.path.exists(file_path):
                logging.info(f"Loading {file} into {table}")
                df = pd.read_csv(file_path)
                df = df.where(pd.notnull(df), None)
                df.to_sql(table, engine, if_exists='replace', index=False)
            else:
                logging.error(f"File {file_path} not found.")

t1_generate = PythonOperator(
    task_id='generate_financial_data',
    python_callable=task_generate_data,
    dag=dag,
)

t2_upload_s3 = PythonOperator(
    task_id='upload_to_s3',
    python_callable=task_upload_to_s3,
    dag=dag,
)

def execute_sql_file(file_path):
    """Executes a DDL SQL file directly using psycopg2 to avoid manual Airflow connection setup."""
    import psycopg2
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "datawarehouse"),
        user=os.getenv("DB_USER", "airflow"),
        password=os.getenv("DB_PASSWORD", "airflow")
    )
    cur = conn.cursor()
    with open(file_path, 'r') as f:
        sql = f.read()
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

def task_create_schema():
    execute_sql_file('/opt/airflow/sql/ddl/create_financial_schema.sql')

t3_create_schema = PythonOperator(
    task_id='create_schema',
    python_callable=task_create_schema,
    dag=dag,
)

t4_load_staging = PythonOperator(
    task_id='load_staging_data',
    python_callable=task_load_staging,
    dag=dag,
)

def task_transform_data():
    import psycopg2
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "datawarehouse"),
        user=os.getenv("DB_USER", "airflow"),
        password=os.getenv("DB_PASSWORD", "airflow")
    )
    cur = conn.cursor()
    
    # Execute ELT load: Insert staging data into final dimensional tables
    
    transform_sql = """
    TRUNCATE TABLE fact_transactions;
    TRUNCATE TABLE dim_accounts;
    TRUNCATE TABLE dim_customers;
    
    INSERT INTO dim_customers (customer_id, first_name, last_name, email, address, city, country, join_date)
    SELECT CAST(customer_id AS VARCHAR(36)), first_name, last_name, email, address, city, country, CAST(join_date AS DATE)
    FROM stg_customers;
    
    INSERT INTO dim_accounts (account_id, customer_id, account_type, balance, open_date, status)
    SELECT CAST(account_id AS VARCHAR(36)), CAST(customer_id AS VARCHAR(36)), account_type, CAST(balance AS NUMERIC), CAST(open_date AS DATE), status
    FROM stg_accounts;
    
    INSERT INTO fact_transactions (transaction_id, account_id, transaction_type, amount, transaction_date, merchant_name, is_fraud)
    SELECT CAST(transaction_id AS VARCHAR(36)), CAST(account_id AS VARCHAR(36)), transaction_type, CAST(amount AS NUMERIC), CAST(transaction_date AS TIMESTAMP), merchant_name, CASE WHEN is_fraud ILIKE 'true' THEN true ELSE false END
    FROM stg_transactions;
    """
    
    cur.execute(transform_sql)
    conn.commit()
    cur.close()
    conn.close()

t5_transform_data = PythonOperator(
    task_id='transform_and_load_facts_dims',
    python_callable=task_transform_data,
    dag=dag,
)

t1_generate >> t2_upload_s3 >> t3_create_schema >> t4_load_staging >> t5_transform_data
