import pandas as pd
import numpy as np

combined_by_type = {}

def fetch_with_retry(url, max_retries=4, wait_seconds=3):
    for attempt in range(max_retries + 1):
        try:
            response = re.get(url)
            if response.status_code == 500:
                print(f"500 error on {url} (attempt {attempt + 1})")
                if attempt < max_retries:
                    time.sleep(wait_seconds)
                    continue
                else:
                    raise Exception("Max retries reached for 500 error")
            response.raise_for_status()
            return response
        except Exception as e:
            if attempt < max_retries:
                print(f"Retrying {url} due to error: {e}")
                time.sleep(wait_seconds)
            else:
                raise

drivers_no = [2, 4, 1, 24, 10, 14, 16, 20, 22, 23, 27, 31, 40, 44, 55, 63, 81, 11, 77]
df_dict = {}

url_meeting = 'https://api.openf1.org/v1/meetings?year=2023&country_name=Singapore'
response = fetch_with_retry(url_meeting)
meetings_df = pd.DataFrame(response.json())


url_session = 'https://api.openf1.org/v1/sessions?meeting_key=1219&session_key=9165&year=2023'
response = fetch_with_retry(url_session)
session_df = pd.DataFrame(response.json())


url_weather = 'https://api.openf1.org/v1/weather?meeting_key=1219&session_key=9165'
response = fetch_with_retry(url_weather)
weather_df = pd.DataFrame(response.json())

url_cardata = 'https://api.openf1.org/v1/car_data?meeting_key=1219&session_key=9165&drs>=9'
response = fetch_with_retry(url_cardata)
car_data_df = pd.DataFrame(response.json())

for driver in drivers_no:
    df_dict[driver] = {}

    api_dict = {
        'drivers': f'https://api.openf1.org/v1/drivers?meeting_key=1219&driver_number={driver}&session_key=9165',
        'pit': f'https://api.openf1.org/v1/pit?session_key=9165&driver_number={driver}',
        'position': f'https://api.openf1.org/v1/position?meeting_key=1219&driver_number={driver}&session_key=9165',
        'race_control': f'https://api.openf1.org/v1/race_control?meeting_key=1219&session_key=9165&driver_number={driver}',
        'laps': f'https://api.openf1.org/v1/laps?session_key=9165&driver_number={driver}&meeting_key=1219',
        'stints': f'https://api.openf1.org/v1/stints?session_key=9165&driver_number={driver}&meeting_key=1219'
    }

    for key, url in api_dict.items():
        try:
            response = fetch_with_retry(url)
            df = pd.DataFrame(response.json())
            df_dict[driver][key] = df
            if not df.empty:
                if key in combined_by_type:
                    combined_by_type[key] = pd.concat([combined_by_type[key], df], ignore_index=True)
                else:
                    combined_by_type[key] = df
            print(f"{key} loaded with {len(df)} rows for driver {driver}")
        except Exception as e:
            print(f"Failed to load {key} for driver {driver}: {e}")

drivers_df = combined_by_type.get('drivers', pd.DataFrame())
pit_df = combined_by_type.get('pit', pd.DataFrame())
position_df = combined_by_type.get('position', pd.DataFrame())
race_control_df = combined_by_type.get('race_control', pd.DataFrame())
laps_df = combined_by_type.get('laps', pd.DataFrame())
stints_df = combined_by_type.get('stints', pd.DataFrame())

race_df = meetings_df.merge(session_df, how='inner', on =['meeting_key'])
race_df = race_df[['meeting_key','session_key', 'meeting_official_name', 'location_x', 'country_name_x','circuit_short_name_x', 'session_name','date_start_x', 'date_end', 'year_x']]
# race_df

drivers_df = drivers_df[((drivers_df['meeting_key']==1219) & (drivers_df['session_key']==9165))]
drivers_df = drivers_df[['driver_number', 'full_name', 'name_acronym', 'team_name', 'country_code', 'session_key', 'meeting_key']]
# drivers_df

race_df = race_df.merge(drivers_df, how='right', on=['meeting_key','session_key'])
# race_df

# laps_df = laps_df.drop(columns=['Unnamed: 0'])
laps_df["date_start"] = pd.to_datetime(laps_df["date_start"], format='mixed')
laps_df['lap_duration'] = pd.to_timedelta(laps_df['lap_duration'], unit='s')

# laps_df[laps_df['lap_duration'].isna()]

# Then format to HH:MM:SS
laps_df['lap_time_str'] = laps_df['lap_duration'].apply(
    lambda x: str(x).split('.')[0]  # removes microseconds
)
laps_df['lap_start_time']=laps_df["date_start"]
laps_df["lap_end_time"] = laps_df["lap_start_time"] + laps_df["lap_duration"]
# laps_df

laps_df['DNF_Flag']=0
for i in range(1, len(laps_df)):  # Start from 1 to avoid index -1 on first row
    if pd.isna(laps_df.loc[i, 'lap_end_time']):
        laps_df.loc[i, 'lap_end_time'] = laps_df.loc[i, 'lap_start_time']
        laps_df['DNF_Flag'][i]=1

# laps_df[laps_df['DNF_Flag']==1]

race_laps_df = laps_df.merge(race_df, how='left', on=['meeting_key', 'session_key', 'driver_number'])
# race_laps_df

pit_df = pit_df[((pit_df['meeting_key']==1219)&(pit_df['session_key']==9165))]
pit_df = pit_df.rename(columns={'date':'pit_date'})
# pit_df

# race_laps_df.shape

race_master_df = race_laps_df.merge(pit_df, on=['meeting_key','session_key','driver_number', 'lap_number'], how='left')

# race_master_df.shape

# race_master_df

# weather_df

# Step 1: Filter and prepare weather data
filtered_weather = weather_df[
    (weather_df['meeting_key'] == 1219) &
    (weather_df['session_key'] == 9165)
].copy()

# Step 2: Parse and sort datetimes
filtered_weather['weather_time'] = pd.to_datetime(filtered_weather['date'], format='mixed', errors='coerce')
filtered_weather = filtered_weather.dropna(subset=['weather_time'])  # Drop rows where parsing failed

race_master_df['lap_end_time'] = pd.to_datetime(race_master_df['lap_end_time'], format='mixed', errors='coerce')
race_master_df = race_master_df.dropna(subset=['lap_end_time'])  # Drop rows with missing end time

# Step 3: Sort both DataFrames
filtered_weather = filtered_weather.sort_values('weather_time')
race_master_df = race_master_df.sort_values('lap_end_time')

# Step 4: Merge based on closest timestamp
race_master_df = pd.merge_asof(
    race_master_df,
    filtered_weather,
    left_on='lap_end_time',
    right_on='weather_time',
    direction='nearest'
)

# Step 6: View results
# race_master_df.head()

race_master_df=race_master_df.rename(columns={'meeting_key_x':'meeting_key','session_key_x':'session_key'})
# race_master_df.head()

# race_master_df

stints_df = stints_df[((stints_df['meeting_key']==1219)&(stints_df['session_key']==9165))]
# stints_df

stints_df['lap'] = stints_df.apply(lambda row: list(range(int(row['lap_start']), int(row['lap_end']) + 1)), axis=1)
expanded_stints_df = stints_df.explode('lap')
expanded_stints_df = expanded_stints_df[['meeting_key', 'session_key', 'driver_number', 'lap', 'compound']].reset_index()
expanded_stints_df = expanded_stints_df.rename(columns={'lap':'lap_number'})
# expanded_stints_df

race_master_df = race_master_df.merge(expanded_stints_df, how='left', on=['meeting_key','session_key','driver_number','lap_number'])
# race_master_df

race_control_df = race_control_df[((race_control_df['meeting_key']==1219)&(race_control_df['session_key']==9165))]
race_control_df = race_control_df.rename(columns={'date':'race_control_date'})
race_control_df = race_control_df.drop(columns=['driver_number'])
# race_control_df

# Step 1: Group messages by lap
flags_grouped = race_control_df.groupby(
    ['meeting_key', 'session_key', 'lap_number']
).agg({
    'flag': lambda x: list(x.dropna()),
    'message': lambda x: list(x.dropna())
}).reset_index()

# Step 2: Merge with race_master
race_master_df = race_master_df.merge(
    flags_grouped,
    how='left',
    on=['meeting_key', 'session_key', 'lap_number']
)

# race_master_df.shape

# race_master_df.head(2)

# Step 1: Ensure datetime types
position_df['date'] = pd.to_datetime(position_df['date'])
race_master_df['lap_start_time'] = pd.to_datetime(race_master_df['lap_start_time'])
race_master_df['lap_end_time'] = pd.to_datetime(race_master_df['lap_end_time'])

# REMOVE THIS LINE — causes row explosion
# race_master_df = race_master_df.merge(position_df, how = 'left', on=['meeting_key', 'session_key', 'driver_number'])

# Step 2: Define position match function (yours is perfect!)
def find_closest_position(driver_row, time_column):
    if pd.isna(driver_row[time_column]):
        return None

    driver_data = position_df[
        (position_df['driver_number'] == driver_row['driver_number']) &
        (position_df['meeting_key'] == driver_row['meeting_key']) &
        (position_df['session_key'] == driver_row['session_key'])
    ].copy()

    driver_data['date'] = pd.to_datetime(driver_data['date'], errors='coerce')
    driver_data = driver_data.dropna(subset=['date'])

    if driver_data.empty:
        return None

    time_diff = (driver_data['date'] - driver_row[time_column]).abs().dropna()
    if time_diff.empty:
        return None

    closest_idx = time_diff.idxmin()
    return driver_data.loc[closest_idx, 'position']

# Step 3: Apply without join
race_master_df['start_position'] = race_master_df.apply(lambda row: find_closest_position(row, 'lap_start_time'), axis=1)
race_master_df['end_position'] = race_master_df.apply(lambda row: find_closest_position(row, 'lap_end_time'), axis=1)

# position_df['date'] = pd.to_datetime(position_df['date'])
# race_master_df['lap_start_time'] = pd.to_datetime(race_master_df['lap_start_time'])
# race_master_df['lap_end_time'] = pd.to_datetime(race_master_df['lap_end_time'])
# position_df.drop(columns=['Unnamed: 0'])

# race_master_df = race_master_df.merge(position_df, how = 'left', on=['meeting_key', 'session_key', 'driver_number'])

# def find_closest_position(driver_row, time_column):
#     # If the lap time is missing, we can't proceed
#     if pd.isna(driver_row[time_column]):
#         print(f"[SKIP] Missing {time_column} for driver {driver_row['driver_number']}")
#         return None

#     # Filter position data
#     driver_data = position_df[
#         (position_df['driver_number'] == driver_row['driver_number']) &
#         (position_df['meeting_key'] == driver_row['meeting_key']) &
#         (position_df['session_key'] == driver_row['session_key'])
#     ].copy()

#     driver_data['date'] = pd.to_datetime(driver_data['date'], errors='coerce')
#     driver_data = driver_data.dropna(subset=['date'])

#     if driver_data.empty:
#         print(f"[EMPTY DRIVER DATA] driver={driver_row['driver_number']} session={driver_row['session_key']} meeting={driver_row['meeting_key']}")
#         return None

#     # Compute time difference safely
#     time_diff = (driver_data['date'] - driver_row[time_column]).abs().dropna()

#     if time_diff.empty:
#         print(f"[EMPTY TIME DIFF] for driver {driver_row['driver_number']} at {driver_row[time_column]}")
#         return None

#     closest_idx = time_diff.idxmin()
#     return driver_data.loc[closest_idx, 'position']

# race_master_df['start_position'] = race_master_df.apply(lambda row: find_closest_position(row, 'lap_start_time'), axis=1)
# race_master_df['end_position'] = race_master_df.apply(lambda row: find_closest_position(row, 'lap_end_time'), axis=1)
# race_master_df[['driver_number', 'lap_start_time', 'lap_end_time', 'start_position', 'end_position']].head()

# race_master_df.shape

# car_data_df.head()

car_data_df['date'] = pd.to_datetime(car_data_df['date'], format='mixed')
car_metrics = []

for _, row in race_master_df.iterrows():
    # Filter car_data_df for same driver, session, meeting, and before lap_end_time
    car_slice = car_data_df[
        (car_data_df['driver_number'] == row['driver_number']) &
        (car_data_df['session_key'] == row['session_key']) &
        (car_data_df['meeting_key'] == row['meeting_key']) &
        (car_data_df['date'] <= row['lap_end_time'])
    ]

    if not car_slice.empty:
        # Get the latest record before lap_end_time
        latest_data = car_slice.loc[car_slice['date'].idxmax()]
        car_metrics.append({
            'rpm': latest_data['rpm'],
            'speed': latest_data['speed'],
            'n_gear': latest_data['n_gear'],
            'throttle': latest_data['throttle'],
            'brake': latest_data['brake'],
            'drs': latest_data['drs']
        })
    else:
        # No data found, fill with NaNs or 0s
        car_metrics.append({
            'rpm': None, 'speed': None, 'n_gear': None,
            'throttle': None, 'brake': None, 'drs': None
        })

# Add these metrics to race_master_df
race_master_df[['rpm', 'speed', 'n_gear', 'throttle', 'brake', 'drs']] = pd.DataFrame(car_metrics)

# race_master_df.shape

# race_master_df.head(5)

# team_radio_df[((team_radio_df['meeting_key']==1219)&(team_radio_df['session_key']==9165))]

# race_master_df['driver_number'].unique()

# Step 1: Sort properly by lap and end time (leader first)
race_master_df = race_master_df.sort_values(by=['lap_number', 'lap_end_time']).reset_index(drop=True)

# Step 2: Gap to leader (P1)
race_master_df['gap_to_leader'] = race_master_df.groupby('lap_number')['lap_end_time'].transform(lambda x: x - x.min())

# Step 3: Interval to previous driver (P2 to P1, P3 to P2, ...)
race_master_df['interval_lap_start'] = race_master_df.groupby('lap_number')['lap_end_time'].diff()
race_master_df['interval_lap_end'] = race_master_df.groupby('lap_number')['lap_start_time'].diff()


# View the result
# race_master_df[['lap_number', 'driver_number', 'lap_start_time', 'lap_end_time',
#                 'interval_lap_start', 'interval_lap_end', 'gap_to_leader']].head(20)

race_master_df.rename(columns={'full_name':'driver_full_name'})

race_master_df.to_csv('ads.csv')

"""##Lap start and end time

"""



# race_master_df.columns

# # Make sure datetime columns are in proper dtype
# intervals_df["date"] = pd.to_datetime(intervals_df["date"],format='mixed')
# race_master_df["lap_end_time"] = pd.to_datetime(race_master_df["lap_end_time"])

# # Sort both by time (and ensure consistent sorting by driver as well)
# intervals_df = intervals_df.sort_values(["driver_number", "date"])
# race_master_df = race_master_df.sort_values(["driver_number", "lap_end_time"])

# # Perform nearest merge on lap_end_time ~ date within each driver
# merged_intervals = pd.merge_asof(
#     race_master_df,
#     intervals_df,
#     by="driver_number",
#     left_on="lap_end_time",
#     right_on="date",
#     direction="nearest",
#     tolerance=pd.Timedelta("2s")  # Adjust if needed (try 1s, 3s, etc.)
# )
# merged_intervals

