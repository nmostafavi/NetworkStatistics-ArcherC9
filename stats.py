#!/usr/bin/env python3

import argparse
import base64
import json
import requests

TIMEOUT = 10  # seconds

def parse_statistics(request, statistics):
    # Quick and dirty string parser that processes the HTML response to obtain: 
    # 1. The raw statistics data on this page, and 
    # 2. The number of pages the total set of data is spread across.
    num_pages = 1
    parser_state = None
    for line in request.iter_lines():
        line = line.decode('utf-8')
        if parser_state == None:
            if line.startswith('var statList = new Array('):
                # Reached beginning of statList data
                parser_state = 'parsing statList'
                continue
            if line.startswith('var PageListPara = new Array('):
                # Reached beginning of PageListPara data
                parser_state = 'parsing PageListPara'
                continue
        elif parser_state == 'parsing statList':
            if line.endswith(');'):
                # Reached end of statList data
                parser_state = None
                continue
            # Parse this row of new data
            fields = line.split(', ')
            hw_address = fields[2].replace('"', '')
            bytes_transferred = int(fields[4])
            statistics[hw_address] = bytes_transferred
        elif parser_state == 'parsing PageListPara':
            # Only interested in the first integer value in PageListPara.
            num_pages = int(line.split(',')[0])
            # Finished parsing the final bit of data we needed.
            break
    return num_pages

def parse_dhcp_list(request, hostnames, ip_addresses):
    parser_state = None
    for line in request.iter_lines():
        line = line.decode('utf-8')
        if parser_state == None:
            if line.startswith('var DHCPDynList = new Array('):
                # Reached beginning of DHCPDynList data
                parser_state = 'parsing DHCPDynList'
                continue
        elif parser_state == 'parsing DHCPDynList':
            if line.endswith(');'):
                # Reached end of DHCPDynList data. Done.
                break
            fields = line.split(', ')
            hostname = fields[0].replace('"', '')
            hw_address = fields[1].replace('"', '')
            ip_address = fields[2].replace('"', '')
            hostnames[hw_address] = hostname
            ip_addresses[hw_address] = ip_address

def setup_session(username, password):
    session = requests.Session()
    credentials = username + ':' + password
    credentials = base64.b64encode(credentials.encode('utf-8'))
    session.cookies.set('Authorization', 'Basic ' + str(credentials, 'utf-8'))
    return session

def make_request(session, url, params={}):
    try:
        return session.get(url=url, params=params, timeout=TIMEOUT)
    except requests.exceptions.ConnectionError as e:
        print('Connection error.')
        print(e)
    except requests.exceptions.Timeout:
        print('Timed out.')
    except requests.exception.RequestException as e:
        print(e)
    return None

def fetch_statistics(address, session, statistics):
    url = 'http://' + address + '/userRpm/SystemStatisticRpm.htm'
    params = { 
        'Num_per_page': 100,  # Max of 100 results at a time can be returned by the firmware
        'sortType': 1,  # Sort by IP address to hopefully get stable pagination
        'Goto_page': 1,  # Page 1 of n
        'interval': 60,  # Seems to influence how frequently the table is populated with new data
        }
    request = make_request(session, url, params)
    if not request:
        return False
    num_pages = parse_statistics(request, statistics)

    # Automatically fetch any subsequent pages to obtain all remaining data
    if num_pages > 1:
        for page in range(2, num_pages+1):
            params['Goto_page'] = page
            request = make_request(session, url, params)
            if not request:
                return False
            parse_statistics(request, statistics)

    return True  # Success

def fetch_dhcp_list(address, session, hostnames, ip_addresses):
    url = 'http://' + address + '/userRpm/AssignedIpAddrListRpm.htm'
    request = make_request(session, url)
    if not request:
        return False
    parse_dhcp_list(request, hostnames, ip_addresses)
    return True  # Success

def main(args):
    session = setup_session(args.username, args.password)

    # Fetch data
    statistics = {}
    fetch_statistics(args.address, session, statistics)

    hostnames = {}
    ip_addresses = {}
    fetch_dhcp_list(args.address, session, hostnames, ip_addresses)

    # Sort statistics in ascending order of bytes transferred
    statistics = dict(sorted(statistics.items(), key=lambda t: t[1], reverse=True))

    data = []
    for hw_address, bytes_transferred in statistics.items():
        hostname = hostnames.get(hw_address, '')
        ip_address = ip_addresses.get(hw_address, '')
        data.append([hw_address, ip_address, hostname, bytes_transferred])
    
    if args.outfile:
        # Write to file silently
        with open(args.outfile, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    else:
        # Print a thinned subset of info to stdout
        bytes_total = 0
        for hw_address, bytes_transferred in statistics.items():
            bytes_total += bytes_transferred
            megabytes_transferred = int(bytes_transferred/1024/1024)
            hostname = hostnames.get(hw_address, '')
            ip_address = ip_addresses.get(hw_address, '')
            if (megabytes_transferred > 0):
                print('{} | {:15.15s} | {:17.17s} | {:,.0f} MB'.format(hw_address, ip_address, hostname, megabytes_transferred))
        print('Total: {:,.0f} MB'.format(bytes_total/1024/1024))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', action='store', dest='address', help='Host address (IP or hostname) of the router. (default: \'192.168.0.1\')', default='192.168.0.1', required=False)
    parser.add_argument('-u', '--username', action='store', dest='username', help='Username used to log into the router. (default: \'admin\')', default='admin', required=False)
    parser.add_argument('-p', '--password', action='store', dest='password', help='Password used to log into the router. (default: \'admin\')', default='admin', required=False)
    parser.add_argument('-o', '--outfile', action='store', dest='outfile', help='Destination file path to write the latest router statistics snapshot to.', required=False)
    args = parser.parse_args()
    main(args)