
import compress
import random

def test_string(s):
    res = compress.simulate_all(s)
    if res:
        h, l, hy = res['huffman'], res['lzw'], res['hybrid']
        if hy < h and hy < l:
             return True, h, l, hy
    return False, 0, 0, 0

# Try constructing a winner
# Large count of a few patterns
best_win = None
for i in range(1, 10):
    for repeat in [1000, 2000, 3000]:
        s = ("abcde" * i + "fghij" * (10-i)) * repeat
        win, h, l, hy = test_string(s)
        if win:
            best_win = (s, h, l, hy)
            break
    if best_win: break

if best_win:
    print("WINNER FOUND!")
    print(f"H: {best_win[1]}, L: {best_win[2]}, HY: {best_win[3]}")
    # print(f"Sample: {best_win[0][:100]}...")
else:
    print("No winner found in structured search.")

# Try biased distribution of repeats
s = ("A"*100 + "B"*10 + "C"*2) * 500
win, h, l, hy = test_string(s)
if win:
    print(f"WINNER! O: {len(s)}, H: {h}, L: {l}, HY: {hy}")
else:
    print(f"FAIL! O: {len(s)}, H: {h}, L: {l}, HY: {hy}")

