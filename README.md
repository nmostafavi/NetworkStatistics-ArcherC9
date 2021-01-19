# BandwidthMonitor-ArcherC9
Fetch bandwidth usage data from TP-LINK Archer C9 router

## About
This script will fetch network traffic statistics from the web interface of the TP-LINK Archer C9 router. In order for statistics to be collected by the router, NAT hardware acceleration (i.e. the "NAT Boost" setting) needs to be turned off in the router's configuration. 

I have written this script in order to compare my internally-gathered bandwidth usage statistics against measurements provided by my ISP. Please keep in mind that the data gathered likely includes all LAN traffic, and sadly may not be accurate for measurement of 
WAN throughput.

## Requirements
This script is written for Python 3. To install the required libraries, run: 
```python3 -m pip install -r requirements.txt```

## How to use
Simply run the script providing your router's address, username, and password provided as arguments, e.g. `./stats.py -a 192.168.1.1 -u root -p password`. By default, it will print a quick summary of throughput statistics in ascending order:
```
48-58-E8-BA-60-26: 1,710 MB
49-2F-37-0B-9D-B6: 977 MB
FE-B7-18-E6-5F-FE: 868 MB
2E-91-09-E5-75-03: 802 MB
A5-56-1D-92-D1-53: 537 MB
81-74-F3-01-A1-E7: 491 MB
5B-B0-60-03-42-8D: 138 MB
EE-5A-54-01-55-4A: 52 MB
21-F9-47-25-1E-D1: 16 MB
02-65-4D-A7-3B-30: 8 MB
AB-48-05-61-91-5B: 7 MB
69-57-10-7F-44-32: 5 MB
8D-A0-93-AC-C5-20: 5 MB
EA-7E-4C-2C-78-F2: 2 MB
19-38-2C-30-DB-A7: 2 MB
```

If an output file path is specified, it will silently write to disk a more comprehensive summary of bytes transferred, in JSON format.

By default, the script will attempt to use a default address of `192.168.1.1`, with username `admin` and password `admin`.

```
usage: stats.py [-h] [-a ADDRESS] [-u USERNAME] [-p PASSWORD] [-o OUTFILE]

optional arguments:
  -h, --help            show this help message and exit
  -a ADDRESS, --address ADDRESS
                        Host address (IP or hostname) of the router. (default: '192.168.1.1')
  -u USERNAME, --username USERNAME
                        Username used to log into the router. (default: 'admin')
  -p PASSWORD, --password PASSWORD
                        Password used to log into the router. (default: 'admin')
  -o OUTFILE, --outfile OUTFILE
                        Destination file path to write the latest router statistics snapshot
                        to.
```
