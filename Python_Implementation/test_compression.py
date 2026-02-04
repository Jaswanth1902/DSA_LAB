
import compress
import os

input_file = 'example_server.log'
output_file = 'example_server.log.lzh'

if os.path.exists(input_file):
    print(f"Compressing {input_file}...")
    compress.compress_file(input_file, output_file)
    
    orig_size = os.path.getsize(input_file)
    comp_size = os.path.getsize(output_file)
    
    ratio = (1 - comp_size/orig_size) * 100
    
    print("-" * 30)
    print(f"Original Size:   {orig_size / (1024*1024):.2f} MB ({orig_size} bytes)")
    print(f"Compressed Size: {comp_size / 1024:.2f} KB ({comp_size} bytes)")
    print(f"Reduction:       {ratio:.2f}%")
    print("-" * 30)
else:
    print("Example log file not found.")
