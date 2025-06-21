import requests
import pandas as pd
import os
from dotenv import load_dotenv
import json
from google.cloud import firestore
from google.oauth2 import service_account
import time
from datetime import datetime, timedelta, date

load_dotenv()
TOKEN = os.getenv("TOKEN")
USER_ID = os.getenv("USER_ID")
PWD = os.getenv("PWD")

class StockDataFetcher:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.finmindtrade.com/api/v4/data"
        self.data = []
        
    def fetch_data(self, stock_id, start_date, end_date):
        """
        Fetch stock data for a given stock ID and date range
        
        Args:
            stock_id (str): The stock ID to fetch data for
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            tuple: (DataFrame containing stock data, status code)
        """
        print(f"Currently Fetching: {stock_id}")
        parameters = {
            "dataset": "TaiwanStockPrice",
            "data_id": stock_id[1:],
            "start_date": start_date,
            "end_date": end_date,
            "token": self.token
        }
        
        try:
            response = requests.get(self.base_url, params=parameters)
            data = response.json()
            status = data["status"]
            df = pd.DataFrame(data["data"])
            df = df[["date", "open", "close", "max", "min"]]
            self.data.append(df)
            return df, status
        except Exception as e:
            print(f"Error fetching data for {stock_id}: {str(e)}")
            return None, None


class DateFetcher:
    def __init__(self, db_client):
        """
        Initialize the DateFetcher with Firestore client
        
        Args:
            db_client: Firestore client instance
        """
        self.db = db_client
        self.collection_name = "date_margin"
        self.document_name = "date_margin_data"
        self.date_margin = None
    
    def fetch_date_data(self):
        """
        Fetch data from Firestore collection 'date_margin' and document 'date_margin_data'
        
        Returns:
            dict: The document data from Firestore
        """
        try:
            doc_ref = self.db.collection(self.collection_name).document(self.document_name)
            doc = doc_ref.get()
            
            if doc.exists:
                self.date_margin = doc.to_dict()
                return self.date_margin
            else:
                print(f"No document found at {self.collection_name}/{self.document_name}")
                return None
                
        except Exception as e:
            print(f"Error fetching data from Firestore: {str(e)}")
            return None
    
    def update_date_data(self, selected_stock, end_date):
        """Update data in Firestore collection 'date_margin' and document 'date_margin_data'"""
        try:
            for i in range(len(selected_stock)):
                if self.date_margin[selected_stock[i]]["e"] >= "2025-05-01": # ensure stock that is already out of market is not updated
                    self.date_margin[selected_stock[i]]["e"] = end_date
            doc_ref = self.db.collection(self.collection_name).document(self.document_name)
            doc_ref.set(self.date_margin, merge=True)
            print("Data successfully updated in Firestore")
        except Exception as e:
            print(f"Error updating data in Firestore: {str(e)}")

def load_selected_stocks(status: int):
    """Load selected stocks from JSON file"""
    try:
        if status == 1:
            with open("stock_list_1.json", "r") as f:
                return json.load(f)
        else:
            with open("stock_list_2.json", "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading selected stocks: {str(e)}")
        return {}

def update_stock_data(stock_id, stock_data, db):
    """Update stock data in Firestore"""
    try:
        # Convert DataFrame to dictionary format
        stock_dict = {}
        for _, row in stock_data.iterrows():
            stock_dict[row['date']] = {
                'o': row['open'],
                'c': row['close'],
                'mn': row['min'],
                'mx': row['max']
            }
        
        # Upload to Firestore
        db.collection("test_stock").document(stock_id).set(stock_dict, merge=True)
        print(f"Successfully updated data for stock {stock_id}")
    except Exception as e:
        print(f"Error updating stock data for {stock_id}: {str(e)}")

def main():
    # Initialize Firestore
    key_path = r"firestore-credential.json"
    with open(key_path, "r") as f:
        info = json.load(f)
    credentials = service_account.Credentials.from_service_account_info(info)
    db = firestore.Client(credentials=credentials)

    # End Date
    end_date = date.today()
    end_date = end_date.strftime("%Y-%m-%d")

    # Initialize fetchers
    date_fetcher = DateFetcher(db)
    stock_fetcher = StockDataFetcher(TOKEN)

    # Get current date range from Firestore
    date_range = date_fetcher.fetch_date_data()
    if not date_range:
        print("No date range data found")
        return
    
    with open("status.txt") as f:
        status = int(f.readline())

    stock_list = load_selected_stocks(status)
    stock_list = stock_list[:10]

    status = 2 if status == 1 else 1

    with open("status.txt", "w") as f:
        f.write(str(status))

    # Update date
    # date_fetcher.update_date_data(stock_list, end_date)

    # Process each stock
    for stock in stock_list:
        print(f"\nProcessing stock: {stock}")
        
        # Get current end date for the stock
        current_end_date = date_range[stock]["e"]

        # print(current_end_date)
        current_end_date_obj = datetime.strptime(current_end_date, "%Y-%m-%d")

        # Subtract 3 days
        start_date_obj = current_end_date_obj - timedelta(days=14)

        # Convert back to string
        start_date = start_date_obj.strftime("%Y-%m-%d")

        # Fetch new data
        df, status = stock_fetcher.fetch_data(stock, start_date, current_end_date)

        if df is not None:
            # Update stock data in Firestore
            update_stock_data(stock, df, db)
            
            # Wait between API calls
            time.sleep(2)
        else:
            print(f"Failed to fetch data for stock {stock}")

if __name__ == "__main__":
    main()


