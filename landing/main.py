

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

#%% Part 3 - Extractor
def cleaner(page):
    #scale down the problem
    html = str(page) 
    begin = html.find('\\n<tr class="table-row" style="cursor: pointer;"')
    end = html.find("</small></td>\\n</tr> </tbody>\\n", begin)
    rawpagereduced = (html[begin:end])
    #Split the string up into rows
    df = rawpagereduced.split("/td>\\n</tr>")
    #remove the tip 
    for element in df:
        if element.find("TIPS!") != -1:
            df.remove(element)
    return df

def splitter(df):
    #split the strings into columns
    seperator = ";"
    index = 0
    for element in df:
        element = element.replace('\\n<tr class="table-row" style="cursor: pointer;" data-href="', '')
        element = element.replace('">\\n', seperator)
        element = element.replace('</small></b><br />', seperator)
        element = element.replace('\\n', seperator)
        element = element.replace(';">', seperator)
        element = element.replace('</b><br /><small>', seperator)
        element = element.replace('</small><', '')
        df[index] = element
        index +=1
    df = pd.DataFrame(df)
    df.columns = ["Name"]
    df = df["Name"].str.split(';', expand = True)
    df.columns = ["Wadress", "Name", "Adress", "Colour", "Price", "Date Entered"]
    df['Date Collected'] = date.today()
    return df
def misc(df):
    #can remove the ugly parts, such as <small> and make the letters swedish (å ä ö)
    df = df.replace(to_replace = ['<td>', '<b>', '<small>', '</td>', '<b style="color:'], value = '', regex = True)
    df['Price'] = df['Price'].replace('kr', '', regex = True)
    df = df.replace('\xc3\xa5','å', regex = True)
    return df
print("functions defined")


def scrape_pages(extract_timestamp):
    #%% Run through all pages and get each price into a row
    html_list = ""
    last_iteration_failed = False
    for iteration in range(1, 5):
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
            break
    html_list + "___data_scraped_at_"+ str(extract_timestamp) + "___"
    return html_list

def fetch_data_to_bucket(FILE_NAME):
    html_list = scrape_pages(extract_timestamp)

    # Upload raw data to GCS
    storage_client = storage.Client(project = PROJECT_NAME)
    bucket = storage_client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(FILE_NAME)
    blob.upload_from_string(html_list, content_type='text/plain; charset=utf-8')

    print(f"Data saved to {FILE_NAME} in bucket {BUCKET_NAME}")

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
        fetch_data_to_bucket(FILE_NAME)
        load_data_to_bq(FILE_NAME)
        # Must return an explicit HTTP response so the server knows it succeeded
        return "Pipeline executed successfully!", 200
    except Exception as e:
        print(f"Pipeline error: {str(e)}")
        return f"Error: {str(e)}", 500
#run_pipeline()



