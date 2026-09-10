

#%% load in a text file with the latest date that the webpage was scraped
#"C:\\programming shit\\webscraping bensin"
# time
from datetime import date
import datetime as datetime
import time

# data prep
import pandas as pd    

# URL information
from urllib.request import Request, urlopen
import urllib

# GCP
from google.cloud import storage, bigquery
import functions_framework

extract_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BUCKET_NAME =  "webscrape-petrol-raw-data" # Make sure this matches your bucket name exactly
FILE_NAME = f"raw_data_{extract_timestamp}.txt"
PROJECT_NAME = 'petrol-webscrape'

def load_data_to_bq(FILE_NAME):
    # Configuration
    PROJECT_ID = "petrol-webscrape" # Replace with your project ID
    DATASET_ID = "b_petrol_webscrape_raw" # TBD: ADD HERE???
    TABLE_ID = "b_petrol_webscrape_raw" # TBD: ADD HERE???
    BUCKET_NAME = "webscrape-petrol-raw-data"
    # Replace with the actual filename from your bucket (e.g., train_data_20260705_211300.json)
    #FILE_NAME = "train_data_20260722_115035.json" 
    client = bigquery.Client(project = PROJECT_ID)

    # Define the table reference
    table_ref = client.dataset(DATASET_ID).table(TABLE_ID)

    # CLEAN DATA HERE - TRANSFORM
    #TBD: ADD HERE



@functions_framework.http
def run_pipeline(request):
    try:
        load_data_to_bq(FILE_NAME)
        # Must return an explicit HTTP response so the server knows it succeeded
        return "Pipeline executed successfully!", 200
    except Exception as e:
        print(f"Pipeline error: {str(e)}")
        return f"Error: {str(e)}", 500
#run_pipeline()



