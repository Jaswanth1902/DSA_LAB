
import os
import datetime

def generate_log_file(filename, size_mb):
    print(f"Generating {size_mb}MB log file: {filename}...")
    target_size = size_mb * 1024 * 1024
    
    # Common log patterns
    levels = ["INFO", "ERROR", "DEBUG", "WARN"]
    messages = [
        "User login successful for user_id: ",
        "Database connection established to cluster-01",
        "GET /api/v1/resource HTTP/1.1 200",
        "Failed to parse request body: invalid JSON",
        "Cache hit for key: user_profile_",
        "Worker process started successfully"
    ]
    
    with open(filename, 'w') as f:
        current_size = 0
        while current_size < target_size:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            level = levels[current_size % len(levels)]
            msg = messages[current_size % len(messages)]
            line = f"[{timestamp}] {level}: {msg}{current_size % 100}\n"
            f.write(line)
            current_size += len(line)
            
    actual_size = os.path.getsize(filename)
    print(f"Generated file size: {actual_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    generate_log_file("example_server.log", 10)
