#!/usr/bin/env python3

import argparse
import os
import stats
import time

UINT32_MAX = 4294967295  # max number of bytes that the router statistics page can display before it overflows
POLL_INTERVAL = 5  # seconds

# State variables
total_bytes_transferred = 0
last_num_hw_addresses = 0
outfile = None
outfile_last_opened = None
outfile_base_filename = ''

def write_header(delta_statistics):
    # Write CSV header: ,hwaddr1,hwaddr2,hwaddr3,...,\n
    global last_num_hw_addresses
    filepath = 'logs/' + outfile_base_filename + ' header.csv'
    print('Writing header file: ' + filepath)
    if not os.path.exists('logs'):
        os.makedirs('logs')
    with open(filepath, 'w') as f:
        f.write(',')
        for hw_addr in delta_statistics:
            f.write(hw_addr)
            f.write(',')
        f.write('\n')
    last_num_hw_addresses = len(delta_statistics)

""" Automatically opens a new outfile at the start of each day.
"""
def open_outfile(base_filename):
    global outfile
    global outfile_last_opened
    global outfile_base_filename
    today = time.strftime('%d')

    if outfile and outfile_last_opened != today:
        # Close yesterday's outfile
        outfile.close()
        outfile = None

    if not outfile:
        # Open today's outfile
        filepath = 'logs/' + base_filename + '.csv'
        print('Writing new log file: ' + filepath)
        if not os.path.exists('logs'):
            os.makedirs('logs')
        outfile = open(filepath, 'w', buffering=1)
        outfile_last_opened = today
        outfile_base_filename = base_filename
        return True  # New outfile opened

    return False

""" Writes out data to disk in CSV format. The CSV's header is kept in a separate file for ease of writing.
    Each row contains a comma separated list of bytes sent since the last row was written. The CSV header
    maintains an ordered list of each hardware address, corresponding to the columns of the data CSV file.
    To open in spreadsheet software (e.g. Excel) simply prepend the header file's contents to the beginning
    of the data CSV file.
"""
def write_data(delta_statistics):
    # Write out deltas of bandwidth consumed per mac address as a new row in the csv.
    # Keep the header of the csv as a separate file to make it easier to append should new values need to be added.
    global outfile
    timestamp = time.strftime('%Y-%m-%d %H%M%S')

    # Open new outfile if needed
    if open_outfile(timestamp) or len(delta_statistics) > last_num_hw_addresses:
        # Rewrite the header if needed
        write_header(delta_statistics)

    # Write CSV data entry: timestamp,deltabytes1,deltabytes2,deltabytes3,...,\n
    outfile.write(timestamp)
    outfile.write(',')
    for _, delta_bytes_transferred in delta_statistics.items():
        outfile.write(str(delta_bytes_transferred))
        outfile.write(',')
    outfile.write('\n')

def main(args):
    global total_bytes_transferred
    session = stats.setup_session(args.username, args.password)

    # Get baseline reading
    previous_statistics = {}
    stats.fetch_statistics(args.address, session, previous_statistics)

    while True:
        # Pre-populate each dictionary with starting data. This allows each dict to maintain a consistent key
        # order, which ultimately allows the final written CSV to maintain its column order.
        delta_statistics = {}
        current_statistics = {}
        for hw_address, previous_bytes_transferred in previous_statistics.items():
            delta_statistics[hw_address] = 0
            current_statistics[hw_address] = previous_bytes_transferred

        # Fetch current statistics from router
        stats.fetch_statistics(args.address, session, current_statistics)
        if not current_statistics:
            print("Failed to fetch statistics.")
            time.sleep(POLL_INTERVAL)
            continue

        # Here is where you might want to note any hardware addresses that have dropped out from the router's data
        # since the last time the data was collected. Knowing which MAC addresses are no longer being tracked by the
        # router could be useful for cleaning up data logs when a new CSV file is created at the start of each day.
        # It would also solve issues should a device suddenly stop being tracked, then start being tracked again at
        # a later time, which would cause a momentary blip (such as inaccuracy due to overcounting) in the data.

        # Process the statistics data
        for hw_address, current_bytes_transferred in current_statistics.items():
            previous_bytes_transferred = previous_statistics.get(hw_address, 0)
            delta_bytes_transferred = 0
            if hw_address in previous_statistics and current_bytes_transferred < previous_bytes_transferred:
                # Value has wrapped around to zero since the last time we checked due to an integer overflow bug
                # in the router's firmware. Router rolls over to 0 once it counts UINT32_MAX bytes.
                delta_bytes_transferred = UINT32_MAX - previous_bytes_transferred + current_bytes_transferred
            else:
                delta_bytes_transferred = current_bytes_transferred - previous_bytes_transferred
            delta_statistics[hw_address] = delta_bytes_transferred
            total_bytes_transferred += delta_bytes_transferred
        previous_statistics = current_statistics

        # Print total bytes transferred
        print('Total: {:,.0f} MB'.format(total_bytes_transferred/1024/1024))

        # Log data to disk
        write_data(delta_statistics)

        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', action='store', dest='address', help='Host address (IP or hostname) of the router. (default: \'192.168.0.1\')', default='192.168.0.1', required=False)
    parser.add_argument('-u', '--username', action='store', dest='username', help='Username used to log into the router. (default: \'admin\')', default='admin', required=False)
    parser.add_argument('-p', '--password', action='store', dest='password', help='Password used to log into the router. (default: \'admin\')', default='admin', required=False)
    args = parser.parse_args()
    main(args)