#!/usr/bin/env python3

import argparse
import stats
import time

UINT32_MAX = 4294967295  # max number of bytes that the router statistics page can display before it overflows
POLL_INTERVAL = 5  # seconds

def write_data(delta_statistics):
    # Periodically open a new file if necessary to split the data, e.g. one file per day.
    # Write out deltas of bandwidth consumed per mac address as a new row in the csv.
    # Keep the header of the csv as a separate file to make it easier to append should new values need to be added.
    filename_template = time.strftime('%Y-%m-%d {}.csv')
    header_filename = filename_template.format('header')
    body_filename = filename_template.format('data')
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    # TODO: see if we have a set of files already open for today. If so, reuse their file handles.
    # If the day has rolled over, close the old file and open a new one.

    # if len(delta_statistics) > num_hw_addresses:
        # A new hardware address has been added since the last log entry; append it to the CSV header.
        # TODO: rewrite CSV header: ,hwaddr1,hwaddr2,hwaddr3,...\n

    # TODO: write CSV data entry: timestamp,deltabytes1,deltabytes2,deltabytes3,...\n

def main(args):
    session = stats.setup_session(args.username, args.password)

    cumulative_statistics = {}
    previous_statistics = {}

    # Get baseline reading
    stats.fetch_statistics(args.address, session, previous_statistics)

    while True:
        # Fetch current statistics from router
        current_statistics = {}
        stats.fetch_statistics(args.address, session, current_statistics)
        if not current_statistics:
            print("Failed to fetch statistics.")
            time.sleep(POLL_INTERVAL)
            continue

        # Copy over all previously encountered hardware addresses to the delta_statistics dict.
        # This allows the final written csv file's columns to remain in stable order.
        delta_statistics = {}
        for hw_address in cumulative_statistics:
            delta_statistics[hw_address] = 0

        # Process the statistics data
        for hw_address, current_bytes_transferred in current_statistics.items():
            previous_bytes_transferred = previous_statistics.get(hw_address, 0)
            delta_bytes_transferred = 0
            if current_bytes_transferred < previous_bytes_transferred:
                # Value has wrapped around to zero since the last time we checked due to an integer overflow bug
                # in the router's firmware. Router rolls over to 0 once it counts UINT32_MAX bytes.
                delta_bytes_transferred = UINT32_MAX - previous_bytes_transferred + current_bytes_transferred
            else:
                delta_bytes_transferred = current_bytes_transferred - previous_bytes_transferred
            delta_statistics[hw_address] = delta_bytes_transferred
            cumulative_statistics[hw_address] = delta_bytes_transferred + cumulative_statistics.get(hw_address, 0)
        previous_statistics = current_statistics

        # Print total bytes transferred
        total = 0
        for hw_address, bytes_transferred in cumulative_statistics.items():
            total += bytes_transferred
        print('Total: {:,.0f} MB'.format(total/1024/1024))

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