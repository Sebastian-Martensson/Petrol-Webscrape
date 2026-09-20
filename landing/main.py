

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

def scrape_pages(extract_timestamp):
    #%% Run through all pages and get each price into a row
    html_list = ""
    max_retries = 5

    for iteration in range(1, 25):
        delay = 20
        page_successful = False
        
        for retry_i in range(max_retries):
            try:
                print(f"Trying page {iteration} (Attempt {retry_i + 1}/{max_retries})")
                base = "https://bensinpriser.nu/stationer/95/alla/alla/"
                webpage = base + str(iteration)
                
                req = Request(webpage, headers={'User-Agent': 'Mozilla/5.0'})
                page = urlopen(req).read()
                html = str(page) 
                html_list += f"___page{iteration}___" + html
                
                page_successful = True
                break  # Exit retry loop on success
                
            except Exception:
                time.sleep(delay)
                print(f"Failed page {iteration} on attempt {retry_i + 1}. Waiting {delay}s...")
                delay *= 2
                
        # If all retries failed for this page, stop the outer loop entirely
        if not page_successful:
            print(f"Page {iteration} failed all retries. Stopping scraper.")
            break
    return html_list

def fetch_data_to_bucket(FILE_NAME, html_list):
    #html_list = scrape_pages(extract_timestamp)

    # Upload raw data to GCS
    storage_client = storage.Client(project = PROJECT_NAME)
    bucket = storage_client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(FILE_NAME)
    blob.upload_from_string(html_list, content_type='text/plain; charset=utf-8')

    print(f"Data saved to {FILE_NAME} in bucket {BUCKET_NAME}")



@functions_framework.http
def run_pipeline(request):
    try:
        html_list = scrape_pages(extract_timestamp)
        fetch_data_to_bucket(FILE_NAME, html_list)
        #load_data_to_bq(FILE_NAME) # TBD: Move to staging folder
        # Must return an explicit HTTP response so the server knows it succeeded
        return "Pipeline executed successfully!", 200
    except Exception as e:
        print(f"Pipeline error: {str(e)}")
        return f"Error: {str(e)}", 500
#run_pipeline()



