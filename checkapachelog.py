import re
from datetime import datetime

# Input and output file paths
input_file = 'C:/develop/proj/simpleapp2/temp/access.log'
output_file = 'temp/cleaned.log'

# Set the target date you want to filter by (YYYY-MM-DD)
target_date = datetime(2024, 12, 10)

# Regular expression to extract the date/time portion from the log line.
# The log line format is typically: 
# `IP - - [DD/Mon/YYYY:HH:MM:SS +TZ] "REQUEST ..."`
# We'll capture `DD/Mon/YYYY:HH:MM:SS +TZ` inside the brackets.
date_pattern = re.compile(r'\[(\d{2}\/[A-Za-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} [+\-]\d{4})\]')

with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
    for line in infile:
        # Check if line contains the unwanted pattern
        if '/SCHOOL/' in line:
            # Skip lines containing this pattern
            continue
        
        # Extract the datetime string from the line
        match = date_pattern.search(line)
        if not match:
            # If no date found, skip or handle as needed
            continue

        date_str = match.group(1)
        # Parse the date using strptime with the given format:
        # Format is: DD/Mon/YYYY:HH:MM:SS +TZ
        log_datetime = datetime.strptime(date_str, "%d/%b/%Y:%H:%M:%S %z")

        # Filter by date (e.g., only include lines from target_date)
        # Convert the timezone-aware datetime to a naive date if needed,
        # or just compare the date component:
        if log_datetime.date() == target_date.date():
            outfile.write(line)
