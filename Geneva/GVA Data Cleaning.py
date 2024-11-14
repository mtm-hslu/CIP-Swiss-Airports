import pandas as pd
import glob
from pathlib import Path

# Load all CSV files
files = glob.glob("./data/*.csv")
dfs = []

for file in files:
    try:
        df = pd.read_csv(file)
        if df.empty:
            print(f"File {file} is empty, skipping.")
            continue

        # Fill in the column flight_type with arrival or departure
        if "arrivals" in file.lower():
            df['flight_type'] = 'arrival'
            df.rename(columns={'origin': 'foreign_airport'}, inplace=True)
        elif "departures" in file.lower():
            df['flight_type'] = 'departure'
            df.rename(columns={'destination': 'foreign_airport'}, inplace=True)
        else:
            print(f"File {file} doesn't contain 'arrivals' or 'departures' in its name, skipping.")
            continue

        dfs.append(df)

    except Exception as e:
        print(f"Could not read {file}: {e}")

# Concatenate all DataFrames
if dfs:
    combined_df = pd.concat(dfs, ignore_index=True)

    # Translate French city names to English so all values correspond
    translation_dict = {
        'Francfort': 'Frankfurt',
        'Beyrouth': 'Beirut',
        'Bruxelles': 'Brussels',
        'Athènes': 'Athens',
        'Lisbonne': 'Lisbon',
        'Londres': 'London',
        'Montréal': 'Montreal',
        'Barcelone': 'Barcelona',
        'Varsovie': 'Warsaw',
        'Copenhague': 'Copenhagen',
        'Séville': 'Seville',
        'Caire': 'Cairo',
        'Djeddah': 'Jeddah',
        'Édimbourg': 'Edinburgh',
        'Malte': 'Malta',
        'Grande Canarie': 'Gran Canaria',
        'Héraklion': 'Heraklion',
        'Palerme': 'Palermo',
        'Alger': 'Algiers',
        'RBA': 'Rabat',
        'Palma de Mallorca': 'Palma de Mallorca',
        'Naples': 'Naples',
        'BRI': 'Bari',
        'Figari': 'Figari',
        'Ibiza': 'Ibiza'
    }
    combined_df['foreign_airport'] = combined_df['foreign_airport'].replace(translation_dict)

    # Extract 'scheduled' and 'actual' times from the 'time' column
    combined_df['scheduled'] = combined_df['time'].str.extract(r'(\d{2}:\d{2})')
    combined_df['actual'] = combined_df['time'].str.extract(r'\d{2}:\d{2}(\d{2}:\d{2})$')
    combined_df['actual'] = combined_df['actual'].fillna(combined_df['scheduled'])

    # Drop time and expected columns since the data is not clean
    combined_df.drop(columns=['time', 'expected'], inplace=True)

    # Convert 'scrape_time' to datetime if necessary
    combined_df['scrape_time'] = pd.to_datetime(combined_df['scrape_time'], errors='coerce')

    # Filter data until and including Friday, 8 November 2024
    filter_date = pd.Timestamp("2024-11-08")
    combined_df = combined_df[combined_df['scrape_time'] <= filter_date]

    # Sort by 'scrape_time' to ensure the latest entries are at the end
    combined_df.sort_values(by='scrape_time', ascending=True, inplace=True)

    # Drop duplicates, keeping the latest entry for each unique flight
    combined_df = combined_df.drop_duplicates(subset=['scheduled', 'foreign_airport', 'airline', 'flight_type'], keep='last')

    # Data Quality Checks

    # Check for gaps/missing data from 22.10.2024 to 09.11.2024
    expected_dates = pd.date_range(start="2024-10-22", end="2024-11-09")
    available_dates = pd.to_datetime(combined_df['scrape_time']).dt.date.unique()
    available_dates = pd.Series(available_dates)
    missing_dates = expected_dates.difference(available_dates)

    if missing_dates.empty:
        print("No gaps found, data is available for all expected dates.")
    else:
        print(f"Missing dates: {missing_dates}")

    # Check if arrivals and departures data are both present for each date
    for date in expected_dates:
        arrivals = combined_df[
            (combined_df['flight_type'] == 'arrival') & (combined_df['scrape_time'].dt.date == date.date())]
        departures = combined_df[
            (combined_df['flight_type'] == 'departure') & (combined_df['scrape_time'].dt.date == date.date())]

        if arrivals.empty:
            print(f"Missing arrivals data for {date.date()}")
        if departures.empty:
            print(f"Missing departures data for {date.date()}")

    # Check if columns show appropriate datatypes and change if needed
    print("Column datatypes:")
    print(combined_df.dtypes)

    # Ensure 'scheduled' and 'actual' are strings, 'scrape_time' is datetime
    assert combined_df['scheduled'].dtype == 'object'
    assert combined_df['actual'].dtype == 'object'
    assert pd.api.types.is_datetime64_any_dtype(combined_df['scrape_time'])

    # Check if values lie in the expected range for 'scheduled' and 'actual' times
    valid_time_format = r'^[0-2][0-9]:[0-5][0-9]$'
    invalid_scheduled_times = combined_df[~combined_df['scheduled'].str.match(valid_time_format)]
    invalid_actual_times = combined_df[~combined_df['actual'].str.match(valid_time_format)]

    if not invalid_scheduled_times.empty:
        print("Invalid scheduled times:")
        print(invalid_scheduled_times[['scheduled']])

    if not invalid_actual_times.empty:
        print("Invalid actual times:")
        print(invalid_actual_times[['actual']])

    # Calculate, identify and flag extreme delta values
    combined_df['scheduled_dt'] = pd.to_datetime(combined_df['scheduled'], format='%H:%M', errors='coerce')
    combined_df['actual_dt'] = pd.to_datetime(combined_df['actual'], format='%H:%M', errors='coerce')
    combined_df['delta'] = ((combined_df['actual_dt'] - combined_df['scheduled_dt']).dt.total_seconds() / 60).astype(
        int)

    # Extract date part and combine with 'actual' and 'scheduled' to create new datetime
    combined_df['actual_date'] = (combined_df['scrape_time'].dt.strftime('%Y-%m-%d') +
                                  ' ' + combined_df['actual'])
    combined_df['scheduled_date'] = (combined_df['scrape_time'].dt.strftime('%Y-%m-%d') +
                                  ' ' + combined_df['scheduled'])
    # Convert to datetime type
    combined_df['actual_date'] = pd.to_datetime(combined_df['actual_date'])
    combined_df['scheduled_date'] = pd.to_datetime(combined_df['scheduled_date'])

    # Drop the temporary datetime columns after calculation
    combined_df.drop(columns=['scheduled_dt', 'actual_dt'], inplace=True)

    # Drop unnecessary columns
    combined_df.drop(columns=['status', 'scrape_time', 'scheduled','actual'], inplace=True)

    # Add local airport in the DataFrame
    combined_df['local_airport'] = "Geneva"

    # Rename Geneva columns
    combined_df.rename(columns={'flight_type': 'Type', 'local_airport': 'LocalAirport',
                              'foreign_airport': 'ForeignAirport', 'scheduled_date': 'PlannedDate',
                              'actual_date': 'ActualDate', 'delta': 'Delay', 'airline': 'Airline'}, inplace=True)
    # Ensure columns are in the desired order
    combined_df = combined_df[['Type', 'LocalAirport', 'ForeignAirport', 'Airline', 'PlannedDate', 'ActualDate', 'Delay']]

    # Bring values in uppercase for consistency
    combined_df['Type'] = combined_df['Type'].str.upper()
    combined_df['LocalAirport'] = combined_df['LocalAirport'].str.upper()
    combined_df['ForeignAirport'] = combined_df['ForeignAirport'].str.upper()
    combined_df['Airline'] = combined_df['Airline'].str.upper()

    # Save the cleaned DataFrame
    output_file = Path("data/combined_cleaned_data.csv")
    combined_df.to_csv(output_file, index=False)
    print("Combined and cleaned data saved.")

else:
    print("No valid CSV files found or loaded.")
