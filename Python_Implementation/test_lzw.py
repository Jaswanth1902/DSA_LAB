from compress import lzw_compress
import struct

def test_lzw():
    data = b"TOBEORNOTTOBEORTOBEORNOT"
    compressed = lzw_compress(data)
    
    # Analyze codes
    count = len(compressed) // 2
    codes = struct.unpack(f'<{count}H', compressed)
    print(f"Input len: {len(data)}")
    print(f"Codes: {codes}")
    print(f"Compressed bytes: {len(compressed)}")
    
    # Expected LZW behavior check
    # TOBEORNOT... should compress well.
    
if __name__ == "__main__":
    test_lzw()
