#!/usr/bin/python3
"""
This script fetches public holidays for Victoria, Australia from a .ics file and merges
them with custom holidays provided in a YAML file. The merged holiday list is then written
to an output text file, skipping holidays that occur before today or fall on weekends 
(Saturdays and Sundays).

Features:
- Downloads the Victorian public holidays from the provided .ics file URL.
- Optionally reads custom holidays from a YAML file (specified via the command line).
- Filters out holidays that fall before today and those that are on weekends.
- Merges public holidays and custom holidays, and writes them to an output file.

How to Use:
1. Basic usage (uses default file paths for custom holidays and output):
   $ python get_holidays.py

2. Specify custom paths for the custom holidays file and the output holidays file:
   $ python get_holidays.py --custom_holidays_file path/to/custom_holidays.yml --holidays_txt_file path/to/holidays.txt

Command-Line Arguments:
- --custom_holidays_file: Path to the custom holidays YAML file (default: 'custom_holidays.yml').
- --holidays_txt_file: Path to the output holidays text file (default: 'holidays.txt').

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
from datetime import datetime, date
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
    - A list of custom holidays in 'YYYY-MM-DD' format. If the file is missing or empty, returns an empty list.
    """
    if os.path.exists(custom_holidays_file):
        with open(custom_holidays_file, 'r') as file:
            try:
                custom_holidays = yaml.safe_load(file)
                if custom_holidays:
                    # Ensure all custom holidays are strings in 'YYYY-MM-DD' format
                    return [str(holiday) for holiday in custom_holidays]
                else:
                    print("Custom holidays file is empty.")
                    return []
            except yaml.YAMLError as e:
                print(f"Error reading custom holidays file: {e}")
                return []
    else:
        print(f"Custom holidays file '{custom_holidays_file}' does not exist.")
        return []

# Download and parse the public holidays from the .ics file
def fetch_public_holidays():
    """
    Downloads and parses public holidays from the .ics file for Victoria, Australia.
    
    Returns:
    - A list of public holidays in 'YYYY-MM-DD' format, excluding weekends and dates before today.
    """
    response = requests.get(url)
    if response.status_code == 200:
        ics_content = response.content
        calendar = icalendar.Calendar.from_ical(ics_content)
        holidays = []
        today = date.today()

        for component in calendar.walk():
            if component.name == "VEVENT":
                event_date = component.get('DTSTART').dt
                if isinstance(event_date, (datetime, date)):
                    # Format the date as 'YYYY-MM-DD'
                    formatted_date = event_date.strftime('%Y-%m-%d')

                    # Add to holidays list only if it's not in the past and not on a weekend
                    if event_date >= today and event_date.weekday() not in (5, 6):
                        holidays.append(formatted_date)

        return holidays
    else:
        print("Failed to download the .ics file")
        return []

# Main function to merge custom and public holidays and write to holidays.txt
def main(custom_holidays_file, holidays_txt_file):
    """
    Main function that merges public holidays with custom holidays and writes the result to a text file.
    
    Args:
    - custom_holidays_file: Path to the YAML file containing custom holidays.
    - holidays_txt_file: Path to the output file where the merged holidays will be written.
    """
    # Fetch public holidays
    public_holidays = fetch_public_holidays()

    # Load custom holidays
    custom_holidays = load_custom_holidays(custom_holidays_file)

    # Merge the two holiday lists (custom holidays take precedence)
    all_holidays = set(public_holidays + custom_holidays)

    # Write the merged holidays to holidays.txt
    if all_holidays:
        with open(holidays_txt_file, "w") as file:
            for holiday in sorted(all_holidays):
                file.write(f"{holiday}\n")
        print(f"Holidays (custom and public) written to {holidays_txt_file}")
    else:
        print("No holidays found.")

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Fetch and merge public and custom holidays")
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

    args = parser.parse_args()

    # Call the main function with parsed arguments
    main(args.custom_holidays_file, args.holidays_txt_file)