import time
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# GCP
from google.cloud import storage
import functions_framework

BUCKET_NAME = "webscrape-petrol-raw-data"
PROJECT_NAME = 'petrol-webscrape'

def scrape_pages(extract_timestamp):
    base = "https://bensinpriser.nu/stationer/95/alla/alla/"
    headers = {
        "User-Agent": "Petrol-Webscrape/1.0 (personal project; contact: your@email.com)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
    }
    max_pages = 25
    max_retries = 3
    pause_between_pages = 5
    inital_delay = 10

    html_list = ""
    blocked = False
    reached_end = False

    for page_no in range(1, max_pages + 1):
        delay = inital_delay
        page = None

        for attempt in range(1, max_retries + 1):
            try:
                print(f"Trying page {page_no} (attempt {attempt}/{max_retries})")
                req = Request(base + str(page_no), headers=headers)
                page = urlopen(req, timeout=30).read()
                break                                   # success

            except HTTPError as e:
                if e.code == 403:
                    print(f"403 Forbidden on page {page_no}. Blocked, stopping.")
                    blocked = True
                    break                               # no point retrying
                if e.code == 404:
                    print(f"Page {page_no} not found, assuming that was the last page.")
                    reached_end = True
                    break
                print(f"HTTP {e.code} on page {page_no}")

            except (URLError, TimeoutError) as e:
                print(f"Network problem on page {page_no}: {e}")

            if attempt < max_retries:                   # only reached when we should retry
                print(f"Waiting {delay}s before retrying...")
                time.sleep(delay)
                delay *= 2

        if blocked or reached_end:
            break
        if page is None:
            print(f"Page {page_no} failed all {max_retries} attempts. Stopping.")
            break
        if b'class="cp-row"' not in page:               # site may return 200 with an empty list
            print(f"Page {page_no} has no stations, stopping.")
            break

        html_list += f"___page{page_no}___" + str(page)
        time.sleep(pause_between_pages)

    print(f"Scraped {html_list.count('___page')} pages. Blocked: {blocked}")
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
if __name__ == "__main__":
    # Local testing only. Cloud Functions ignores this block.
    print(run_pipeline(None))