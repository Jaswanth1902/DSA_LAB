import urllib.request
import urllib.parse
import sys
import os
import json

url = "http://127.0.0.1:5000/process"
filepath = "test_file.txt"
with open(filepath, "w") as f:
    f.write("A" * 100)

boundary = '----------Boundary123456789'
data = []
data.append(f'--{boundary}')
data.append('Content-Disposition: form-data; name="mode"')
data.append('')
data.append('compress')
data.append(f'--{boundary}')
data.append(f'Content-Disposition: form-data; name="file"; filename="{filepath}"')
data.append('Content-Type: text/plain')
data.append('')
with open(filepath, 'r') as f:
    data.append(f.read())
data.append(f'--{boundary}--')
data.append('')

body = '\r\n'.join(data).encode('utf-8')
headers = {'Content-Type': f'multipart/form-data; boundary={boundary}'}

req = urllib.request.Request(url, data=body, headers=headers, method='POST')
try:
    with urllib.request.urlopen(req) as response:
        print(f"Status: {response.status}")
        print(response.read().decode('utf-8'))
        
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
