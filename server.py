#!/usr/bin/env python3
import json
import os
from flask import Flask, send_from_directory

app = Flask(__name__, static_url_path='', static_folder='web')

@app.route('/')
def root():
    return app.send_static_file('index.html')

@app.route('/logs/<path:filename>')
def static_logs(filename):
    return send_from_directory(app.root_path + '/logs/', filename)

@app.route('/logs/manifest.json')
def manifest():
    # Do a quick and dirty pass over the files list.
    files = os.listdir('logs')
    files.sort()
    
    data = {}
    for filename in files:
        if '.csv' not in filename:
            continue
        timestamp = filename[:17]
        if timestamp not in data:
            data[timestamp] = {}
        if 'header' in filename:
            data[timestamp]['header'] = filename
        else:
            data[timestamp]['data'] = filename

    return json.dumps(data, indent=2)

if __name__ == '__main__':
    app.run()