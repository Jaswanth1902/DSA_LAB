import heapq
import sys
import struct
import os

# --- Huffman Decompression ---

class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
    
    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(frequency):
    priority_queue = [HuffmanNode(char, freq) for char, freq in frequency.items()]
    heapq.heapify(priority_queue)

    while len(priority_queue) > 1:
        left = heapq.heappop(priority_queue)
        right = heapq.heappop(priority_queue)

        merged = HuffmanNode(None, left.freq + right.freq)
        merged.left = left
        merged.right = right

        heapq.heappush(priority_queue, merged)

    return priority_queue[0]

def huffman_decompress_bytes(file_handle):
    header_data = file_handle.read(5) 
    if len(header_data) < 5:
        return b"" 

    total_chars, unique_chars = struct.unpack('<LB', header_data)
    
    if unique_chars == 0 and total_chars > 0:
        unique_chars = 256

    frequency = {}
    for _ in range(unique_chars):
        entry_data = file_handle.read(5)
        char_code, freq = struct.unpack('<BI', entry_data)
        frequency[char_code] = freq

    root = build_huffman_tree(frequency)

    # Flatten tree for speed
    # We will use lists as simple arrays: left_children, right_children, values
    # Node 0 is root.
    
    # 1. Assign IDs and build arrays
    next_node_id = 1
    # Max nodes = 2 * unique_chars - 1. Safe upper bound is enough.
    # Initial capacity
    capacity = unique_chars * 2 + 100
    left_children = [-1] * capacity
    right_children = [-1] * capacity
    node_values = [-1] * capacity
    
    # helper to populate
    # returns node_id
    def flatten(node):
        nonlocal next_node_id, left_children, right_children, node_values
        
        if node is None:
            return -1
            
        curr_id = next_node_id
        next_node_id += 1
        
        # Check capacity (dynamic resize if needed, though unlikely with calculated bound)
        if curr_id >= len(left_children):
             extension = [-1] * len(left_children)
             left_children.extend(extension)
             right_children.extend(extension)
             node_values.extend(extension)
        
        if node.left is None and node.right is None: # Leaf
            left_children[curr_id] = -1 # Marker
            right_children[curr_id] = -1
            node_values[curr_id] = node.char
        else:
            # Internal
            l_id = flatten(node.left)
            r_id = flatten(node.right)
            left_children[curr_id] = l_id
            right_children[curr_id] = r_id
            
        return curr_id

    # Reset root ID to 0 for convenience? Actually our helper uses 1-based or we can just start.
    # Let's simple start next_node_id = 0
    next_node_id = 0
    
    def flatten_root(node):
        nonlocal next_node_id
        if node is None: return -1
        
        my_id = next_node_id
        next_node_id += 1
        
        if node.left is None and node.right is None:
            left_children[my_id] = -2 # -2 indicates Leaf
            node_values[my_id] = node.char
        else:
            l_id = flatten_root(node.left)
            r_id = flatten_root(node.right)
            left_children[my_id] = l_id
            right_children[my_id] = r_id
        return my_id

    root_id = flatten_root(root)
    
    extracted_chars = 0
    curr = root_id
    
    output = bytearray()
    
    # Buffered reading for speed
    chunk_size = 65536 # 64KB
    
    while extracted_chars < total_chars:
        # Read a large chunk of bytes efficiently
        chunk = file_handle.read(chunk_size)
        if not chunk:
            break
            
        for byte_val in chunk:
            # Unrolled bit loop for performance
            # Bit 7
            bit = (byte_val >> 7) & 1
            if bit == 0: curr = left_children[curr]
            else:        curr = right_children[curr]
            
            if left_children[curr] == -2: # Leaf
                output.append(node_values[curr])
                extracted_chars += 1
                curr = root_id
                if extracted_chars >= total_chars: break

            # Bit 6
            bit = (byte_val >> 6) & 1
            if bit == 0: curr = left_children[curr]
            else:        curr = right_children[curr]
            
            if left_children[curr] == -2:
                output.append(node_values[curr])
                extracted_chars += 1
                curr = root_id
                if extracted_chars >= total_chars: break

            # Bit 5
            bit = (byte_val >> 5) & 1
            if bit == 0: curr = left_children[curr]
            else:        curr = right_children[curr]
            
            if left_children[curr] == -2:
                output.append(node_values[curr])
                extracted_chars += 1
                curr = root_id
                if extracted_chars >= total_chars: break

            # Bit 4
            bit = (byte_val >> 4) & 1
            if bit == 0: curr = left_children[curr]
            else:        curr = right_children[curr]
            
            if left_children[curr] == -2:
                output.append(node_values[curr])
                extracted_chars += 1
                curr = root_id
                if extracted_chars >= total_chars: break

            # Bit 3
            bit = (byte_val >> 3) & 1
            if bit == 0: curr = left_children[curr]
            else:        curr = right_children[curr]
            
            if left_children[curr] == -2:
                output.append(node_values[curr])
                extracted_chars += 1
                curr = root_id
                if extracted_chars >= total_chars: break

            # Bit 2
            bit = (byte_val >> 2) & 1
            if bit == 0: curr = left_children[curr]
            else:        curr = right_children[curr]
            
            if left_children[curr] == -2:
                output.append(node_values[curr])
                extracted_chars += 1
                curr = root_id
                if extracted_chars >= total_chars: break

            # Bit 1
            bit = (byte_val >> 1) & 1
            if bit == 0: curr = left_children[curr]
            else:        curr = right_children[curr]
            
            if left_children[curr] == -2:
                output.append(node_values[curr])
                extracted_chars += 1
                curr = root_id
                if extracted_chars >= total_chars: break

            # Bit 0
            bit = byte_val & 1
            if bit == 0: curr = left_children[curr]
            else:        curr = right_children[curr]
            
            if left_children[curr] == -2:
                output.append(node_values[curr])
                extracted_chars += 1
                curr = root_id
                if extracted_chars >= total_chars: break
            
            # Optimization: If we finished, break early from chunk loop
            if extracted_chars >= total_chars:
                break
    
    return bytes(output)

# --- LZW Decompression ---

def lzw_decompress(data):
    if not data:
        return b""

    count = len(data) // 2
    codes = struct.unpack(f'<{count}H', data)

    dictionary = {i: bytes([i]) for i in range(256)}
    next_code = 256
# --- LZW Decompression ---

def lzw_decompress(data):
    if not data:
        return b""

    count = len(data) // 2
    codes = struct.unpack(f'<{count}H', data)

    # Initialize Dictionary (0-255)
    # We use a list for O(1) integer access because codes are contiguous integers 0...N
    # dictionary[i] = bytes
    
    # Pre-allocate distinct list for performance? Or just append.
    # Since we reset, list is easier to clear.
    
    dictionary = [bytes([i]) for i in range(256)]
    # Reserve slot 256 for CLEAR_CODE (though we don't output bytes for it)
    dictionary.append(b'') 
    
    CLEAR_CODE = 256
    next_code = 257
    MAX_DICT_SIZE = 65535
    
    result = bytearray()
    
    if not codes:
        return b""
        
    # Iterator logic to handle resets
    code_iter = iter(codes)
    
    # Read first code
    try:
        old_code = next(code_iter)
    except StopIteration:
        return b""
        
    # Edge case: File starts with CLEAR_CODE? Unlikely but assume standard LZW.
    while old_code == CLEAR_CODE:
        old_code = next(code_iter)
        
    result.extend(dictionary[old_code])
    
    for code in code_iter:
        if code == CLEAR_CODE:
            # RESET
            dictionary = [bytes([i]) for i in range(256)]
            dictionary.append(b'') # 256
            next_code = 257
            
            # Read next code immediately to restart sequence
            try:
                old_code = next(code_iter)
            except StopIteration:
                break
                
            result.extend(dictionary[old_code])
            continue
            
        if code < len(dictionary):
            entry = dictionary[code]
        elif code == next_code:
            entry = dictionary[old_code] + dictionary[old_code][:1]
        else:
            raise ValueError(f"Bad LZW code: {code}")
        
        result.extend(entry)
        
        # Add new phrase to dictionary
        if next_code < MAX_DICT_SIZE:
             # dictionary[old_code] + entry[0]
             dictionary.append(dictionary[old_code] + entry[:1])
             next_code += 1
            
        old_code = code
        
    return bytes(result)

def decompress_file(input_file, output_file):
    if not os.path.exists(input_file):
        return

    with open(input_file, 'rb') as f:
        # Read Flag
        flag_byte = f.read(1)
        if not flag_byte:
            return 
        
        flag = ord(flag_byte) # 1 or 0
        


        print(f"Decompressing... Mode: {'LZW+Huffman' if flag else 'Huffman Only'}")
        
        # Step 1: Huffman
        huffman_decoded_data = huffman_decompress_bytes(f)
        
        final_data = b""
        
        if flag == 1:
            # Step 2: LZW
            final_data = lzw_decompress(huffman_decoded_data)
        else:
            final_data = huffman_decoded_data
            
        with open(output_file, 'wb') as out:
            out.write(final_data)

    print(f"Decompression complete.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: python {sys.argv[0]} <input_file> <output_file>")
    else:
        decompress_file(sys.argv[1], sys.argv[2])
