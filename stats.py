#!/usr/bin/env python3

import argparse
import base64
import collections
import json
import requests

def parse_request(request, data):
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
            data[hw_address] = bytes_transferred
        elif parser_state == 'parsing PageListPara':
            # Only interested in the first integer value in PageListPara.
            num_pages = int(line.split(',')[0])
            # Finished parsing the final bit of data we needed.
            break
    return num_pages

def fetch_data(address, username, password, data):
    credentials = username + ':' + password
    credentials = base64.b64encode(credentials.encode('utf-8'))
    cookies = { 'Authorization': 'Basic ' + str(credentials, 'utf-8') }
    url = 'http://' + address + '/userRpm/SystemStatisticRpm.htm'
    params = { 
        'Num_per_page': 100,  # Max of 100 results at a time can be returned by the firmware
        'sortType': 1,  # Sort by IP address to hopefully get stable pagination
        'Goto_page': 1,  # Page 1 of n
        'interval': 60,  # Seems to influence how frequently the table is populated with new data
        }
    request = requests.get(url=url, params=params, cookies=cookies)
    num_pages = parse_request(request, data)

    # Automatically fetch any subsequent pages to obtain all remaining data
    if num_pages > 1:
        for page in range(2, num_pages+1):
            params['Goto_page'] = page
            request = requests.get(url=url, params=params, cookies=cookies)
            parse_request(request, data)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', action='store', dest='address', help='Host address (IP or hostname) of the router. (default: \'192.168.1.1\')', default='192.168.1.1', required=False)
    parser.add_argument('-u', '--username', action='store', dest='username', help='Username used to log into the router. (default: \'admin\')', default='admin', required=False)
    parser.add_argument('-p', '--password', action='store', dest='password', help='Password used to log into the router. (default: \'admin\')', default='admin', required=False)
    parser.add_argument('-o', '--outfile', action='store', dest='outfile', help='Destination file path to write the latest router statistics snapshot to.', required=False)
    args = parser.parse_args()

    data = {}
    fetch_data(args.address, args.username, args.password, data)
    
    if args.outfile:
        # Write to file silently
        with open(args.outfile, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    else:
        # Print a thinned subset of info to stdout
        sorted_data = collections.OrderedDict(sorted(data.items(), key=lambda t: t[1], reverse=True))
        for hw_address, bytes_transferred in sorted_data.items():
            megabytes_transferred = int(bytes_transferred/1024/1024)
            if (megabytes_transferred > 0):
                print('{}: {:,.0f} MB'.format(hw_address, megabytes_transferred))

if __name__ == '__main__':
    main()