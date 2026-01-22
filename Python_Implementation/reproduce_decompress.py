import urllib.request
import urllib.parse
import sys
import os
import json

url = "http://127.0.0.1:5000/process"
# The file should have been created by previous script in uploads/
# But wait, app.py saves uploads to 'uploads' folder.
# My previous script sent 'test_file.txt' content.
# The app saved it to 'uploads/test_file.txt' and created 'uploads/test_file.lzh'.

# Now I need to upload 'uploads/test_file.lzh' for decompression.
# I will first read it.

upload_folder = 'uploads'
filename = 'test_file.lzh'
filepath = os.path.join(upload_folder, filename)

if not os.path.exists(filepath):
    print(f"File {filepath} not found. Compression might have failed to save.")
    sys.exit(1)

boundary = '----------BoundaryDecompress'
data = []
data.append(f'--{boundary}')
data.append('Content-Disposition: form-data; name="mode"')
data.append('')
data.append('decompress')
data.append(f'--{boundary}')
data.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"')
data.append('Content-Type: application/octet-stream')
data.append('')
with open(filepath, 'rb') as f:
    # Need to append bytes, so we can't mix with strings easily in data list strategy above
    # Let's switch to bytes construction
    pass

body = bytearray()
body.extend(f'--{boundary}\r\n'.encode('utf-8'))
body.extend('Content-Disposition: form-data; name="mode"\r\n\r\n'.encode('utf-8'))
body.extend('decompress\r\n'.encode('utf-8'))

body.extend(f'--{boundary}\r\n'.encode('utf-8'))
body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode('utf-8'))
# body.extend('Content-Type: application/octet-stream\r\n\r\n'.encode('utf-8'))
# mime type detection isn't critical probably
body.extend(b'\r\n') 

with open(filepath, 'rb') as f:
    body.extend(f.read())

body.extend(b'\r\n')
body.extend(f'--{boundary}--\r\n'.encode('utf-8'))

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
