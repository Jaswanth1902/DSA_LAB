
import compress

def diagnose(s):
    res = compress.simulate_all(s)
    print(f"Original: {res['original']}")
    print(f"Huffman:  {res['huffman']}")
    print(f"LZW:      {res['lzw']}")
    print(f"Hybrid:   {res['hybrid']}")

diagnose("The transition to a digital-first economy has accelerated the demand for intelligent data compression techniques. Hybrid algorithms, such as LZW combined with Huffman coding, offer a powerful solution by leveraging both dictionary-based and statistical redundancies. This simulator allows you to explore how different data patterns respond to these classic yet effective algorithms in real-time.")
# A very repetitive one
diagnose("abc" * 1000)
