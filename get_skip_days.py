"""
This script generates a list of dates where the previous day is a holiday from the source
(public holidays and custom holidays). It also includes any source holidays that fall on a
Friday if they are not already in the skipdays list (holidays.txt). This is useful for
skipping tape backups on days when no one will be in the office to change the tape.

Features:
- Downloads Victorian public holidays from a provided .ics file URL.
- Optionally reads custom holidays from a YAML file (specified via the command line).
- For each date from today onwards, checks if the previous day is a holiday from the source.
- Writes dates where the previous day is a holiday to an output file.
- Excludes weekends and dates before today.
- Adds any source holidays that fall on a Friday to the output.
- Allows customization of the date range via command-line arguments.

How to Use:
1. Basic usage (uses default file paths for custom holidays and output):
   $ python get_holidays.py

2. Specify custom paths for the custom holidays file and the output holidays file:
   $ python get_holidays.py --custom_holidays_file path/to/custom_holidays.yml --holidays_txt_file path/to/holidays.txt

3. Specify the date range:
   $ python get_holidays.py --start_date YYYY-MM-DD --end_date YYYY-MM-DD

Command-Line Arguments:
- --custom_holidays_file: Path to the custom holidays YAML file (default: 'custom_holidays.yml').
- --holidays_txt_file: Path to the output holidays text file (default: 'holidays.txt').
- --start_date: Start date in 'YYYY-MM-DD' format (default: today).
- --end_date: End date in 'YYYY-MM-DD' format (default: last holiday date).

Dependencies:
- requests: Used to download the public holidays .ics file.
- icalendar: Used to parse .ics calendar files.
- yaml: Used to parse custom holidays from a YAML file.

Ensure you have the necessary dependencies installed:
$ pip install requests icalendar pyyaml

Example of `custom_holidays.yml`:
-----------------------------------
# Custom holidays for the organization, in YYYY-MM-DD format
- 2024-12-24  # Christmas Eve
- 2024-12-31  # New Year's Eve
- 2025-01-02  # Day after New Year's Day
- 2025-03-17  # St. Patrick's Day
- 2025-07-04  # Company Anniversary

The custom holidays file should contain each holiday date in 'YYYY-MM-DD' format,
with each date on a new line as part of a YAML list. You can add comments to describe the holidays.
"""

import os
import requests
import icalendar
from datetime import datetime, date, timedelta
import yaml
import argparse

# URL of the .ics file
url = "https://www.vic.gov.au/sites/default/files/2024-09/Victorian-public-holiday-dates_0.ics"

# Function to load custom holidays from the YAML file
def load_custom_holidays(custom_holidays_file):
    """
    Loads custom holidays from a specified YAML file.

    Args:
    - custom_holidays_file: The path to the YAML file containing custom holidays.

    Returns:
    - A set of custom holidays as date objects. If the file is missing or empty, returns an empty set.
    """
    if os.path.exists(custom_holidays_file):
        with open(custom_holidays_file, 'r') as file:
            try:
                custom_holidays = yaml.safe_load(file)
                if custom_holidays:
                    # Convert to date objects
                    return set(datetime.strptime(str(holiday), '%Y-%m-%d').date() for holiday in custom_holidays)
                else:
                    print("Custom holidays file is empty.")
                    return set()
            except yaml.YAMLError as e:
                print(f"Error reading custom holidays file: {e}")
                return set()
    else:
        print(f"Custom holidays file '{custom_holidays_file}' does not exist.")
        return set()

# Function to fetch public holidays from the .ics file
def fetch_public_holidays():
    """
    Downloads and parses public holidays from the .ics file for Victoria, Australia.

    Returns:
    - A set of public holidays as date objects, excluding dates before today.
    """
    response = requests.get(url)
    if response.status_code == 200:
        ics_content = response.content
        calendar = icalendar.Calendar.from_ical(ics_content)
        holidays = set()
        today = date.today()

        for component in calendar.walk():
            if component.name == "VEVENT":
                event_date = component.get('DTSTART').dt
                if isinstance(event_date, datetime):
                    event_date = event_date.date()
                if event_date >= today:
                    holidays.add(event_date)

        return holidays
    else:
        print("Failed to download the .ics file")
        return set()

# Main function to generate the holiday dates
def main(custom_holidays_file, holidays_txt_file, start_date_str=None, end_date_str=None):
    """
    Main function that generates dates where the previous day is a holiday from the source.
    Also includes any source holidays that fall on a Friday.

    Args:
    - custom_holidays_file: Path to the YAML file containing custom holidays.
    - holidays_txt_file: Path to the output file where the dates will be written.
    - start_date_str: Start date as a string in 'YYYY-MM-DD' format.
    - end_date_str: End date as a string in 'YYYY-MM-DD' format.
    """
    # Fetch public holidays
    public_holidays = fetch_public_holidays()

    # Load custom holidays
    custom_holidays = load_custom_holidays(custom_holidays_file)

    # Combine all source holidays
    source_holidays = public_holidays.union(custom_holidays)

    # Set the date range
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = date.today()

    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        if source_holidays:
            end_date = max(source_holidays)
        else:
            end_date = start_date + timedelta(days=365)  # Default to one year ahead if no holidays found

    # Generate dates where the previous day is a holiday from the source
    valid_dates = set()

    current_date = start_date
    while current_date <= end_date:
        previous_day = current_date - timedelta(days=1)
        # Exclude weekends
        if current_date.weekday() < 5:
            if previous_day in source_holidays:
                valid_dates.add(current_date)
        current_date += timedelta(days=1)

    # Additional Rule: Include any source holidays that fall on a Friday
    for holiday in source_holidays:
        if holiday.weekday() == 4:  # Friday
            if holiday >= start_date and holiday <= end_date:
                valid_dates.add(holiday)

    # Write the valid dates to the output file
    if valid_dates:
        with open(holidays_txt_file, "w") as file:
            for holiday in sorted(valid_dates):
                file.write(f"{holiday.strftime('%Y-%m-%d')}\n")
        print(f"Dates have been written to {holidays_txt_file}")
    else:
        print("No dates found.")

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Generate dates where the previous day is a holiday")
    parser.add_argument(
        '--custom_holidays_file',
        type=str,
        default='custom_holidays.yml',
        help="Path to the custom holidays YAML file (default: 'custom_holidays.yml')"
    )
    parser.add_argument(
        '--holidays_txt_file',
        type=str,
        default='holidays.txt',
        help="Path to the output holidays text file (default: 'holidays.txt')"
    )
    parser.add_argument(
        '--start_date',
        type=str,
        default=None,
        help="Start date in YYYY-MM-DD format (default: today)"
    )
    parser.add_argument(
        '--end_date',
        type=str,
        default=None,
        help="End date in YYYY-MM-DD format (default: last holiday date)"
    )

    args = parser.parse_args()

    # Call the main function with parsed arguments
    main(
        args.custom_holidays_file,
        args.holidays_txt_file,
        start_date_str=args.start_date,
        end_date_str=args.end_date
    )
