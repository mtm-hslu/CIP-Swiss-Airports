import pandas as pd
import glob

# Load all CSV files
files = glob.glob("/users/nafisaumar/documents/GenevaAirport/*.csv")
dfs = []

for file in files:
    try:
        df = pd.read_csv(file)
        if df.empty:
            print(f"File {file} is empty, skipping.")
            continue

        if "arrivals" in file.lower():
            df['flight_type'] = 'arrivals'
            df.rename(columns={'origin': 'location'}, inplace=True)  # Rename to unify with departures
        elif "departures" in file.lower():
            df['flight_type'] = 'departures'
            df.rename(columns={'destination': 'location'}, inplace=True)  # Rename to unify with arrivals
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
    combined_df['location'] = combined_df['location'].replace(translation_dict)

    # Extract 'scheduled' and 'actual' times from the 'time' column
    combined_df['scheduled'] = combined_df['time'].str.extract(r'(\d{2}:\d{2})')
    combined_df['actual'] = combined_df['time'].str.extract(r'\d{2}:\d{2}(\d{2}:\d{2})$')
    combined_df['actual'] = combined_df['actual'].fillna(combined_df['scheduled'])

    # Convert 'scrape_time' to datetime if necessary
    combined_df['scrape_time'] = pd.to_datetime(combined_df['scrape_time'], errors='coerce')

    # Filter data until and including Friday, 8 November 2024
    filter_date = pd.Timestamp("2024-11-08")
    combined_df = combined_df[combined_df['scrape_time'] <= filter_date]

    # Sort by 'scrape_time' to ensure the latest entries are at the end
    combined_df.sort_values(by='scrape_time', ascending=True, inplace=True)

    # Drop duplicates, keeping the latest entry for each unique flight
    combined_df = combined_df.drop_duplicates(subset=['scheduled', 'location', 'airline', 'flight_type'], keep='last')

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
            (combined_df['flight_type'] == 'arrivals') & (combined_df['scrape_time'].dt.date == date.date())]
        departures = combined_df[
            (combined_df['flight_type'] == 'departures') & (combined_df['scrape_time'].dt.date == date.date())]

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

    # Flag extreme delays or early arrivals
    combined_df['is_extreme_delay'] = combined_df['delta'] > 120  # More than 5 hours delay
    combined_df['is_extreme_early'] = combined_df['delta'] < -30  # More than 30 minutes early

    if combined_df['is_extreme_delay'].any():
        print("Flights with extreme delays (more than 5 hours):")
        print(combined_df[combined_df['is_extreme_delay']][['scheduled', 'actual', 'delta']])

    if combined_df['is_extreme_early'].any():
        print("Flights with extreme early arrivals (more than 30 minutes early):")
        print(combined_df[combined_df['is_extreme_early']][['scheduled', 'actual', 'delta']])

    # Drop the temporary datetime columns after calculation
    combined_df.drop(columns=['scheduled_dt', 'actual_dt'], inplace=True)

    # Save the cleaned DataFrame
    combined_df.to_csv("/users/nafisaumar/documents/GenevaAirport/combined_cleaned_data.csv", index=False)
    print("Combined and cleaned data saved.")

else:
    print("No valid CSV files found or loaded.")
