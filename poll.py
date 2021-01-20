#!/usr/bin/env python3

import argparse
import stats
import time

UINT32_MAX = 4294967295  # max number of bytes that the router statistics page can display before it overflows
POLL_INTERVAL = 5  # seconds

def main(args):
    session = stats.setup_session(args.username, args.password)

    cumulative_statistics = {}
    previous_statistics = {}

    # Get baseline reading
    stats.fetch_statistics(args.address, session, previous_statistics)

    while True:
        current_statistics = {}
        stats.fetch_statistics(args.address, session, current_statistics)

        for hw_address, current_bytes_transferred in current_statistics.items():
            previous_bytes_transferred = previous_statistics.get(hw_address, 0)

            delta_bytes_transferred = 0
            if current_bytes_transferred < previous_bytes_transferred:
                # Value has wrapped around to zero since the last time we checked due to an integer overflow bug
                # in the router's firmware. Router rolls over to 0 once it counts UINT32_MAX bytes.
                delta_bytes_transferred = UINT32_MAX - previous_bytes_transferred + current_bytes_transferred
            else:
                delta_bytes_transferred = current_bytes_transferred - previous_bytes_transferred

            cumulative_statistics[hw_address] = delta_bytes_transferred + cumulative_statistics.get(hw_address, 0)
        previous_statistics = current_statistics

        total = 0
        for hw_address, bytes_transferred in cumulative_statistics.items():
            total += bytes_transferred
        print('Total: {:,.0f} MB'.format(total/1024/1024))

        # TODO: Write cumulative statistics to disk with a timestamp
        # TODO: Write total to disk also

        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', action='store', dest='address', help='Host address (IP or hostname) of the router. (default: \'192.168.0.1\')', default='192.168.0.1', required=False)
    parser.add_argument('-u', '--username', action='store', dest='username', help='Username used to log into the router. (default: \'admin\')', default='admin', required=False)
    parser.add_argument('-p', '--password', action='store', dest='password', help='Password used to log into the router. (default: \'admin\')', default='admin', required=False)
    args = parser.parse_args()
    main(args)