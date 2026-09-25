import time
from datetime import datetime
from urllib.request import Request, urlopen

# GCP
from google.cloud import storage
import functions_framework

BUCKET_NAME = "webscrape-petrol-raw-data"
PROJECT_NAME = 'petrol-webscrape'

def scrape_pages(extract_timestamp):
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
                
            except Exception as e:
                time.sleep(delay)
                print(f"Failed page {iteration} on attempt {retry_i + 1}. Waiting {delay}s...")
                delay *= 2  # Fixed backoff bug
                
        # If all retries failed for this page, stop the outer loop entirely
        if not page_successful:
            print(f"Page {iteration} failed all retries. Stopping scraper.")
            break
            
    return html_list

def fetch_data_to_bucket(file_name, html_list):
    storage_client = storage.Client(project=PROJECT_NAME)
    bucket = storage_client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(file_name)
    blob.upload_from_string(html_list, content_type='text/plain; charset=utf-8')
    print(f"Data saved to {file_name} in bucket {BUCKET_NAME}")

@functions_framework.http
def run_pipeline(request):
    try:
        # Generate a unique timestamp and filename per execution
        extract_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"raw_data_{extract_timestamp}.txt"
        
        html_list = scrape_pages(extract_timestamp)
        fetch_data_to_bucket(file_name, html_list)
        
        return "Pipeline executed successfully!", 200
    except Exception as e:
        print(f"Pipeline error: {str(e)}")
        return f"Error: {str(e)}", 500