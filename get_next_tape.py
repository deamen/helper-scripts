import os
import datetime
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import argparse
import time
import re

# Function to read the public holidays from a specified file
def get_public_holidays(holiday_file):
    try:
        with open(holiday_file, 'r') as f:
            holidays = [line.strip() for line in f if line.strip()]
        return [datetime.datetime.strptime(date, '%Y-%m-%d').date() for date in holidays]
    except Exception as e:
        print(f"Error reading holiday file {holiday_file}: {e}")
        return []

# Function to determine if today is a public holiday
def is_public_holiday(today, holidays):
    return today in holidays

# Function to calculate the backup pool based on the date
def calculate_backup_pool(today, holidays):
    # Adjust for the backup running after midnight
    backup_day = today + datetime.timedelta(days=1)

    # Skip backup if it's Sunday or a public holiday
    if backup_day.weekday() == 6 or is_public_holiday(backup_day, holidays):
        print("No backup due to Sunday or public holiday.")
        return None

    # First, check for Yearly (first Saturday of February or August)
    if backup_day.weekday() == 5:  # Saturday
        if backup_day.day <= 7 and backup_day.month in [2, 8]:
            return "Yearly"

        # Check for Monthly (first Saturday of each month)
        if backup_day.day <= 7:
            return "Monthly"

        # Otherwise, it's a Weekly backup
        return "Weekly"
    
    # Any other workday is a Daily backup
    return "Daily"

# Function to get the next Bacula tape using a shell command
def get_bacula_next_tape(pool):
    cmd = f'echo "list nextvol job=BackupCatalog pool={pool}" | bconsole | egrep "The next"'
    try:
        result = subprocess.check_output(cmd, shell=True).decode().strip()
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running Bacula command: {e}")
        return None

# Function to extract tape label (e.g., Daily013, Weekly005) from tape_info
def extract_tape_label(tape_info):
    match = re.search(r'(Daily\d+|Weekly\d+|Monthly\d+|Yearly\d+)', tape_info)
    if match:
        return match.group(1)
    return None

# Function to send an email with the tape information
def send_email(sender, recipient, smtp_server, smtp_port, smtp_user, smtp_pass, subject, message_body):
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    # Add the message body
    msg.attach(MIMEText(message_body))

    # Send the email via SMTP
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.sendmail(sender, recipient, msg.as_string())
        print(f"Email sent to {recipient}")
    except Exception as e:
        print(f"Error sending email: {e}")

# Function to get the current date and time in the specified format
def get_formatted_date():
    # Get the current time
    return time.strftime('%a %b %d %H:%M:%S %Z %Y')

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Send Bacula job status via email and determine the backup pool.")
    parser.add_argument('--from', dest='sender', required=True, help="Sender's email address")
    parser.add_argument('--to', dest='recipient', required=True, help="Recipient's email address")
    parser.add_argument('--smtp', dest='smtp_server', required=True, help="SMTP server")
    parser.add_argument('--port', dest='smtp_port', default=587, help="SMTP port (default 587)")
    parser.add_argument('--user', dest='smtp_user', help="SMTP user (optional)")
    parser.add_argument('--pass', dest='smtp_pass', help="SMTP password (optional)")
    parser.add_argument('--holiday-file', dest='holiday_file', required=True, help="Path to the holiday file")

    args = parser.parse_args()

    # Get today's date and holidays from the specified file
    today = datetime.date.today()
    holidays = get_public_holidays(args.holiday_file)

    # Determine which pool to use
    pool = calculate_backup_pool(today, holidays)
    if not pool:
        return  # No backup today

    # Get the next tape for the determined pool
    tape_info = get_bacula_next_tape(pool)
    if tape_info:
        # Extract the tape label (e.g., Daily013, Weekly005)
        tape_label = extract_tape_label(tape_info)
        
        # Get the formatted date
        formatted_date = get_formatted_date()

        # Construct the email subject with the tape label and formatted date
        if tape_label:
            subject = f"Bacula next tape {tape_label} ({formatted_date})"
        else:
            subject = f"Bacula next tape ({formatted_date})"
        
        # Construct the message body with the tape info
        message_body = f"The next tape for pool {pool}: {tape_info}"

        # Send the email with the tape information
        send_email(args.sender, args.recipient, args.smtp_server, args.smtp_port, args.smtp_user, args.smtp_pass, subject, message_body)
    else:
        print(f"Could not retrieve tape info for pool {pool}.")

if __name__ == "__main__":
    main()
