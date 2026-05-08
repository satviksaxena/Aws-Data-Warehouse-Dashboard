import os
import random
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

def generate_customers(num_customers=1000):
    data = []
    for _ in range(num_customers):
        data.append({
            'customer_id': fake.uuid4(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': fake.email(),
            'address': fake.address().replace('\n', ', '),
            'city': fake.city(),
            'country': fake.country(),
            'join_date': fake.date_between(start_date='-5y', end_date='today').isoformat()
        })
    return pd.DataFrame(data)

def generate_accounts(customers_df, max_accounts_per_customer=3):
    data = []
    account_types = ['Checking', 'Savings', 'Credit Card', 'Investment']
    
    for customer_id in customers_df['customer_id']:
        num_accounts = random.randint(1, max_accounts_per_customer)
        for _ in range(num_accounts):
            data.append({
                'account_id': fake.uuid4(),
                'customer_id': customer_id,
                'account_type': random.choice(account_types),
                'balance': round(random.uniform(0, 100000), 2),
                'open_date': fake.date_between(start_date='-5y', end_date='today').isoformat(),
                'status': random.choices(['Active', 'Closed', 'Frozen'], weights=[0.85, 0.1, 0.05])[0]
            })
    return pd.DataFrame(data)

def generate_transactions(accounts_df, num_transactions=10000):
    data = []
    transaction_types = ['Deposit', 'Withdrawal', 'Transfer', 'Payment', 'Fee']
    
    active_accounts = accounts_df[accounts_df['status'] == 'Active']['account_id'].tolist()
    
    if not active_accounts:
        return pd.DataFrame()

    start_date = datetime.now() - timedelta(days=365)
    
    for _ in range(num_transactions):
        data.append({
            'transaction_id': fake.uuid4(),
            'account_id': random.choice(active_accounts),
            'transaction_type': random.choice(transaction_types),
            'amount': round(random.uniform(1, 5000), 2),
            'transaction_date': fake.date_time_between(start_date=start_date, end_date='now').isoformat(),
            'merchant_name': fake.company() if random.random() > 0.5 else None,
            'is_fraud': random.choices([True, False], weights=[0.02, 0.98])[0]
        })
    return pd.DataFrame(data)

def main():
    print("Generating financial data...")
    customers = generate_customers(500)
    accounts = generate_accounts(customers)
    transactions = generate_transactions(accounts, 5000)
    
    # Save to local landing zone
    landing_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'landing')
    os.makedirs(landing_dir, exist_ok=True)
    
    customers_path = os.path.join(landing_dir, 'customers.csv')
    accounts_path = os.path.join(landing_dir, 'accounts.csv')
    transactions_path = os.path.join(landing_dir, 'transactions.csv')
    
    customers.to_csv(customers_path, index=False)
    accounts.to_csv(accounts_path, index=False)
    transactions.to_csv(transactions_path, index=False)
    
    print(f"Data generation complete. Saved to {landing_dir}")

if __name__ == '__main__':
    main()
