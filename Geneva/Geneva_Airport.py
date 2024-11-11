
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Initialize the WebDriver with an existing Chrome instance
def initialize_driver(retries=3, wait_time=5):
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    for attempt in range(retries):
        try:
            return webdriver.Chrome(options=chrome_options)
        except WebDriverException as e:
            logger.error(f"Attempt {attempt + 1}: Failed to connect to the existing Chrome instance: {e}")
            time.sleep(wait_time)
    raise WebDriverException("Could not connect to the Chrome instance after several attempts.")

# Scrape flight data from the Geneva Arrivals and Departures Page
def scrape_flights(driver, url, flight_type):
    driver.get(url)

    # Click on "Show more flights" until all flights are loaded
    while True:
        try:
            show_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "p_lt_ctl07_pageplaceholder_p_lt_ctl00_FlightsList_MoreFlights"))
            )
            driver.execute_script("arguments[0].click();", show_more_button)
            time.sleep(2)
        except TimeoutException:
            logger.info("No more 'Show more flights' button found or timeout.")
            break

    # Get page source and parse with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Extract flight information
    flights = []
    flight_table = soup.find('table', class_='table-tools')
    if not flight_table:
        flight_table = soup.find('table')  # Fallback to any table if class not found
    if flight_table:
        flight_rows = flight_table.find_all('tr')[1:]
        for row in flight_rows:
            columns = row.find_all('td')
            if len(columns) >= 5:
                flight_data = {
                    'time': columns[0].get_text(strip=True),
                    'expected': columns[1].get_text(strip=True),
                    'origin' if flight_type == 'arrivals' else 'destination': columns[2].get_text(strip=True),
                    'airline': columns[3].get_text(strip=True),
                    'status': columns[6].get_text(strip=True),
                    'scrape_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                flights.append(flight_data)

    return flights

# Save flights to CSV
def save_flights_to_csv(flights, flight_type):
    if flights:
        df = pd.DataFrame(flights)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_directory = "/Users/nafisaumar/Documents/GenevaAirport/"
        csv_filename = f"{output_directory}geneva_{flight_type}_{timestamp}.csv"
        df.to_csv(csv_filename, index=False)
        logger.info(f"Data saved to {csv_filename}")
    else:
        logger.error(f"No {flight_type} flight data found.")

# Scraping process
def main():
    try:
        driver = initialize_driver()

        # Scrape arrivals
        arrivals_url = "https://www.gva.ch/en/Site/Passagers/Vols/Informations/Arrivees"
        arrivals = scrape_flights(driver, arrivals_url, "arrivals")
        save_flights_to_csv(arrivals, "arrivals")

        # Scrape departures
        departures_url = "https://www.gva.ch/en/Site/Passagers/Vols/Informations/Departs"
        departures = scrape_flights(driver, departures_url, "departures")
        save_flights_to_csv(departures, "departures")

    except WebDriverException as e:
        logger.error(f"Failed to connect to the existing Chrome instance: {e}")
        raise e
    finally:
        driver.quit()

# Scraping function
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
