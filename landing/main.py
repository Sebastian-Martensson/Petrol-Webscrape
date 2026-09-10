

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
    last_iteration_failed = False
    for iteration in range(1, 25):
        try:
            delay = 20
            max_retries = 5
            for _ in range(max_retries):
                try:
                    print(iteration)
                    base = "https://bensinpriser.nu/stationer/95/alla/alla/"
                    number = str(iteration)
                    webpage = base + number
                    req = Request(webpage, headers={'User-Agent': 'Mozilla/5.0'})
                    page = urlopen(req).read()
                    html = str(page) 
                    html_list = html_list + "___page" + str(iteration) +"___" + html

                    # Break out of the for loop once the page has been successfully scraped
                    break
                except:
                    time.sleep(delay)
                    print(f"Couldn't scrape page {iteration} after {_} tries. Last scrape delayed by {delay} seconds")
                    delay *= 2
        except ValueError:
            print("limit reached")
    html_list = html_list + "___data_scraped_at_"+ str(extract_timestamp) + "___"
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



