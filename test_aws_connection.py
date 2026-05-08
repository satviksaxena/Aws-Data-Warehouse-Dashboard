import os
import boto3
import psycopg2
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_s3_connection():
    logging.info("--- Testing S3 Connection ---")
    bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
    if not bucket_name:
        logging.error("AWS_S3_BUCKET_NAME is not set in .env")
        return False
        
    try:
        logging.info("Initializing boto3 S3 client...")
        # boto3 automatically uses AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY from environment
        s3 = boto3.client('s3')
        
        logging.info(f"Checking access to bucket: {bucket_name}")
        # Test by trying to list the bucket or check if it exists
        response = s3.head_bucket(Bucket=bucket_name)
        logging.info(f"S3 Connection Successful. Successfully accessed bucket '{bucket_name}'.")
        return True
    except Exception as e:
        logging.error(f"S3 Connection Failed: {e}")
        return False

def test_redshift_connection():
    logging.info("\n--- Testing Redshift Connection ---")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "5439")
    dbname = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    
    if not all([host, dbname, user, password]):
        logging.error("Missing one or more Redshift connection variables in .env")
        return False

    try:
        logging.info(f"Attempting to connect to Redshift at {host}:{port}/{dbname} as user '{user}'...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=dbname,
            user=user,
            password=password,
            connect_timeout=10 # fail fast if it hangs
        )
        logging.info("Redshift Connection Successful.")
        
        # Run a simple test query
        logging.info("Running test query (SELECT version())...")
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        logging.info(f"Redshift Version: {version}")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Redshift Connection Failed: {e}")
        logging.info("HINT: Ensure your Redshift Serverless cluster allows inbound traffic from your current IP address (Check the Security Group settings in AWS).")
        return False

if __name__ == "__main__":
    logging.info("Loading environment variables from .env file...")
    load_dotenv()
    
    s3_ok = test_s3_connection()
    rs_ok = test_redshift_connection()
    
    logging.info("\n--- Summary ---")
    if s3_ok and rs_ok:
        logging.info("All AWS connections are working properly.")
    else:
        logging.error("Some connections failed. Please review the errors above.")
