"""
author:    Kethrin Heinze
date:      19.10.2024
"""

import csv
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
import time
from datetime import datetime
from pathlib import Path

# Unified scraping function for both arrivals and departures
def scrape_flights(url, flight_type):
    print(f"Scraping URL: {url}")
    
    # Get the current date and time when the data is scraped
    scraped_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Request (for static content)
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    # Webdriver
    print("*" * 80, "\nScraping with webdriver")

    # headless option for chromedriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    
    # Get the page using Selenium and wait for it to load
    driver.get(url)
    time.sleep(10)
    page = driver.page_source
    driver.quit()

    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(page, 'html.parser')

    print("*" * 80)

    # Find the main flight table
    table = soup.find('table', {'class': 'flights-table is-collapsable show-for-medium'})

    # If table is found, proceed
    if table:
        primary_rows = table.find_all('tr', class_='flights-table-primary')

        # Extract text from a BeautifulSoup element, handling missing or empty values
        def extract_text(element):
            return element.get_text(strip=True) if element else 'N/A'

        # List to store all rows of data
        flight_data = []

        # Iterate through each primary flight row and extract the flight information
        for index, primary_row in enumerate(primary_rows):
            columns = primary_row.find_all('td')

            # Extract flight details from the primary row
            flight_time = extract_text(columns[0])
            expected = extract_text(columns[1])
            destination_or_origin = extract_text(columns[2])
            airline = extract_text(columns[3])
            flight_number = extract_text(columns[4])
            status = extract_text(columns[5])  # Extract full status text
            note = extract_text(columns[6]) if len(columns) > 6 else 'N/A'

            # Add flight type (Arrivals/Departures), flight details, and scraped date to the list
            flight_data.append([flight_type, flight_time, expected, destination_or_origin, airline, flight_number, status, note, scraped_date])

        return flight_data
    else:
        print("Table not found in the page.")
        return []

# URLs for arrivals and departures
arrivals_url = 'https://www.euroairport.com/en/passengers-visitors/arrivals-departures/flights/arrivals.html'
departures_url = 'https://www.euroairport.com/en/passengers-visitors/arrivals-departures/flights/departures.html'

# CSV file to save the data with the actual date it was scraped
csv_filename = Path(f'data/basel_{datetime.now().strftime("%Y-%m-%d")}.csv')

# Create the directory if it doesn't exist
csv_filename.parent.mkdir(parents=True, exist_ok=True)

# List to store all flight data before writing to CSV
all_flights = []

# Scrape arrivals
print("Scraping Arrivals")
all_flights += scrape_flights(arrivals_url, 'Arrivals')

# Scrape departures
print("\nScraping Departures")
all_flights += scrape_flights(departures_url, 'Departures')

# Write data to CSV
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    
    # Write the header
    writer.writerow(['Type', 'Time', 'Expected', 'Origin/Destination', 'Airline', 'Flight Number', 'Status', 'Note', 'Date Scraped'])
    
    # Write all flight data
    writer.writerows(all_flights)

print(f"Data has been saved to {csv_filename}")