import heapq
import os
import sys
import struct
import json

from collections import Counter

# --- LZW Compression (Optimized with Integer Trie) ---

def lzw_compress(data, return_dict=False):
    """
    Compresses a bytes object using LZW with Integer-based Dictionary.
    Returns a bytes object representing a list of 16-bit integers.
    Supports dictionary reset (CLEAR_CODE = 256).
    """
    MAX_DICT_SIZE = 65535 # 16-bit limit
    CLEAR_CODE = 256
    next_code = 257 # Start after 0-255 characters + CLEAR_CODE
    
    # Key: (prefix_code, current_char_byte) -> value: new_code
    dictionary = {}
    
    result = []
    
    if not data:
        return b""
        
    # Start with the first byte
    w = data[0]
    
    for i in range(1, len(data)):
        c = data[i]
        wc_key = (w, c)
        
        if wc_key in dictionary:
            w = dictionary[wc_key]
        else:
            result.append(w)
            
            # Add to dictionary if space permits
            if next_code < MAX_DICT_SIZE:
                dictionary[wc_key] = next_code
                next_code += 1
            else:
                # Dictionary full: Emit Clear Code and Reset
                result.append(CLEAR_CODE)
                dictionary.clear()
                next_code = 257
            
            w = c
            
    # Output the last code
    result.append(w)
    
    packed_data = struct.pack(f'<{len(result)}H', *result)
    
    if return_dict:
        # Convert dictionary to a readable format (string representations)
        readable_dict = {str(k): v for k, v in dictionary.items()}
        # Also include initial 0-255 characters symbolically
        return packed_data, readable_dict, result
        
    return packed_data


# --- Huffman Compression (Optimized) ---

class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq
    
    def to_dict(self):
        node_name = f"'{chr(self.char)}'" if self.char is not None else ""
        if self.char == 10: node_name = "NB" # NewLine 
        if self.char == 32: node_name = "SP" # Space
        
        return {
            "name": node_name,
            "value": self.freq,
            "children": [
                self.left.to_dict() if self.left else None,
                self.right.to_dict() if self.right else None
            ]
        }

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

def build_codes(node, current_val, current_len, codes):
    if node is None:
        return

    if node.char is not None:
        codes[node.char] = (current_val, current_len)
        return

    # Left: 0, Right: 1
    build_codes(node.left, (current_val << 1), current_len + 1, codes)
    build_codes(node.right, (current_val << 1) | 1, current_len + 1, codes)


def huffman_compress_bytes_with_tree(data):
    if not data:
        return b'\x00\x00\x00\x00\x00', None

    # Optimized Frequency Count
    frequency = Counter(data)

    root = build_huffman_tree(frequency)
    
    # Custom cleaner to make D3 happy
    def clean_tree_recursive(node):
        d = { "name": "", "value": node.freq }
        if node.char is not None:
             # Basic ASCII range or Hex
             if 32 <= node.char <= 126:
                 d["name"] = chr(node.char)
             else:
                 d["name"] = f"x{node.char:02X}"
        
        children = []
        if node.left: children.append(clean_tree_recursive(node.left))
        if node.right: children.append(clean_tree_recursive(node.right))
        
        if children:
            d["children"] = children
        return d

    tree_json = clean_tree_recursive(root)

    codes = {}
    build_codes(root, 0, 0, codes)

    total_chars = len(data)
    unique_chars = len(frequency)
    encoded_unique_chars = unique_chars if unique_chars < 256 else 0

    output = bytearray()
    output.extend(struct.pack('<LB', total_chars, encoded_unique_chars))

    for char_code, freq in frequency.items():
        output.extend(struct.pack('<BI', char_code, freq))

    buffer_val = 0
    bits_in_buffer = 0
    append = output.append
    
    # Optimized Bit Packing
    for byte_val in data:
        code, length = codes[byte_val]
        
        # Shift code into the top of the buffer
        buffer_val = (buffer_val << length) | code
        bits_in_buffer += length
        
        # Flush full bytes
        while bits_in_buffer >= 8:
            bits_in_buffer -= 8
            # Extract top 8 bits
            append((buffer_val >> bits_in_buffer) & 0xFF)
            
            buffer_val &= (1 << bits_in_buffer) - 1

    # Flush remaining bits
    if bits_in_buffer > 0:
        # Pad with zeros (shift left to align to byte boundary)
        append((buffer_val << (8 - bits_in_buffer)) & 0xFF)
        
    # Generate binary string for visualization
    binary_str = ""
    for byte_val in data:
        code, length = codes[byte_val]
        binary_str += format(code, f'0{length}b')

    return output, tree_json, binary_str

def compress_file(input_file, output_file):
    if not os.path.exists(input_file):
        return None

    raw_data = b""
    with open(input_file, 'rb') as f:
        raw_data = f.read()

    original_size = len(raw_data)
    if original_size == 0:
        return None

    # Step 1: Try LZW
    lzw_data = lzw_compress(raw_data)
    lzw_size = len(lzw_data)
    
    use_lzw = (lzw_size < original_size)
    hybrid_source_data = lzw_data if use_lzw else raw_data
    
    # Step 2: Huffman
    huffman_output, tree_data, _ = huffman_compress_bytes_with_tree(hybrid_source_data)
    
    # Step 3: Compare with Original
    # flag byte (1) + huffman_output
    final_compressed_size = len(huffman_output) + 1
    
    with open(output_file, 'wb') as out:
        if final_compressed_size < original_size:
            # Compression is efficient
            out.write(b'\x01' if use_lzw else b'\x00')
            out.write(huffman_output)
        else:
            # Fallback to Identity (Raw)
            # Use flag \x02 to indicate raw data
            out.write(b'\x02')
            out.write(raw_data)

    return tree_data

def huffman_compress_only(data):
    """Convenience function for simulation."""
    output, tree, binary_str = huffman_compress_bytes_with_tree(data)
    return len(output), tree, binary_str

def lzw_compress_only(data, return_dict=False):
    """Convenience function for simulation."""
    if return_dict:
        output, dictionary, codes = lzw_compress(data, return_dict=True)
        return output, dictionary, codes
    output = lzw_compress(data)
    return output

def simulate_all(text_input):
    """
    Performs LZW, Huffman, and Hybrid compression on the input text.
    Returns comparison metrics.
    """
    if isinstance(text_input, str):
        data = text_input.encode('utf-8')
    else:
        data = text_input

    original_size = len(data)
    if original_size == 0:
        return None

    # 1. Huffman Only
    huff_size, huff_tree, huff_binary = huffman_compress_only(data)

    # 2. LZW Only
    lzw_data_standalone, lzw_dict, lzw_codes = lzw_compress_only(data, return_dict=True)
    lzw_size = len(lzw_data_standalone)

    # 3. Hybrid (Forced Logic for Simulator)
    # For simulation, we force LZW -> Huffman sequence even if inefficient.
    lzw_data_temp = lzw_compress(data)
    hybrid_source = lzw_data_temp 
    hybrid_huff_output, hybrid_tree, hybrid_binary = huffman_compress_bytes_with_tree(hybrid_source)
    hybrid_size = len(hybrid_huff_output) + 1 # +1 for the flag byte
    use_lzw = True

    # Guaranteed Smallest (Our refinement)
    smallest_size = min(huff_size + 1, hybrid_size) # +1 for flag \x00
    is_raw_best = (original_size <= smallest_size)
    
    if is_raw_best:
        smallest_size = original_size + 1 # +1 for flag \x02
        best_mode = "Identity (Raw)"
    else:
        best_mode = "Hybrid" if hybrid_size <= (huff_size + 1) else "Huffman Only"

    return {
        "original": original_size,
        "huffman": huff_size,
        "huffman_tree": huff_tree,
        "huffman_binary": huff_binary,
        "lzw": lzw_size,
        "lzw_dict": lzw_dict,
        "lzw_codes": lzw_codes,
        "hybrid": hybrid_size,
        "hybrid_tree": hybrid_tree,
        "hybrid_binary": hybrid_binary,
        "lzw_used_in_hybrid": use_lzw,
        "best_possible": min(original_size + 1, smallest_size),
        "best_mode": best_mode
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        pass
    else:
        compress_file(sys.argv[1], sys.argv[2])
