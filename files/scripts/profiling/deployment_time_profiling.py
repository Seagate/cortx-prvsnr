#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import csv
from datetime import datetime
import sys


def info():
    """Brief info on how to use this code."""
    print("""
The script requires exactly 2 arguments in sequence:
1. Input log file
2. CSV output file

Sample command:
 $ python deployment_time_profiling.py input_file output_file.csv
        """)


if len(sys.argv) != 3:
    print("Please provide exactly 2 command line arguments to the code")
    info()
    sys.exit(1)


def read_file():
    """Reads the input/log file and returns a list of lines in the file.
    """

    log_file_path = sys.argv[1]
    log_file = open(log_file_path, "r")
    file_list = log_file.readlines()
    log_file.close()
    return file_list


def get_formatted_time(line):
    """Parse and returns the timestamp and text from a string."""
    # First 23 characters in the line is the timestamp
    # eg: 2021-01-06 17:30:03,575
    date = line[:23]
    # This section of the line from index 33 contains text/brief description.
    text = line[33:-1]
    return datetime.strptime(date, '%Y-%m-%d %H:%M:%S,%f'), text


def display_result(components, time_taken):
    """Prints the result in a tabular format."""
    for i, dur in enumerate(time_taken):
        print(f"{components[i]:<100} | {dur}")
        print(f"{'-'*125}")


# Read the input file.
file_list = read_file()

components = ["Components"]
time_taken = ["Time taken in seconds"]

count = 0
prev_time = None

# Looping through the lines in the file
for line in file_list:
    # Checking if the line contains a timestamp
    if line[0].isdigit():
        temp = []
        curr_time, text = get_formatted_time(line)
        components.append(text)
        if count != 0:
            diff = curr_time - prev_time
            time_taken.append(diff.total_seconds())
        prev_time = curr_time
        count += 1

display_result(components, time_taken)

# Writing the result to a csv file.
output_file_path = sys.argv[2]
rows = zip(components[:-1], time_taken)
with open(output_file_path, "w", newline='') as f:
    writer = csv.writer(f)
    for row in rows:
        writer.writerow(row)

print(f"\nCSV report saved in {output_file_path} file")
