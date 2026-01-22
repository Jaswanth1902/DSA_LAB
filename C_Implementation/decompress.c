#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_TREE_HT 100
#define LZW_DICT_SIZE 4096

// --- Huffman Decoding ---

struct MinHeapNode {
    char data;
    unsigned freq;
    struct MinHeapNode *left, *right;
};

struct MinHeapNode* newNode(char data, unsigned freq) {
    struct MinHeapNode* temp = (struct MinHeapNode*)malloc(sizeof(struct MinHeapNode));
    temp->left = temp->right = NULL;
    temp->data = data;
    temp->freq = freq;
    return temp;
}

struct MinHeap {
    unsigned size;
    unsigned capacity;
    struct MinHeapNode** array;
};

struct MinHeap* createMinHeap(unsigned capacity) {
    struct MinHeap* minHeap = (struct MinHeap*)malloc(sizeof(struct MinHeap));
    minHeap->size = 0;
    minHeap->capacity = capacity;
    minHeap->array = (struct MinHeapNode**)malloc(minHeap->capacity * sizeof(struct MinHeapNode*));
    return minHeap;
}

void swapMinHeapNode(struct MinHeapNode** a, struct MinHeapNode** b) {
    struct MinHeapNode* t = *a;
    *a = *b;
    *b = t;
}

void minHeapify(struct MinHeap* minHeap, int idx) {
    int smallest = idx;
    int left = 2 * idx + 1;
    int right = 2 * idx + 2;

    if (left < minHeap->size && minHeap->array[left]->freq < minHeap->array[smallest]->freq)
        smallest = left;

    if (right < minHeap->size && minHeap->array[right]->freq < minHeap->array[smallest]->freq)
        smallest = right;

    if (smallest != idx) {
        swapMinHeapNode(&minHeap->array[smallest], &minHeap->array[idx]);
        minHeapify(minHeap, smallest);
    }
}

int isSizeOne(struct MinHeap* minHeap) {
    return (minHeap->size == 1);
}

struct MinHeapNode* extractMin(struct MinHeap* minHeap) {
    struct MinHeapNode* temp = minHeap->array[0];
    minHeap->array[0] = minHeap->array[minHeap->size - 1];
    --minHeap->size;
    minHeapify(minHeap, 0);
    return temp;
}

void insertMinHeap(struct MinHeap* minHeap, struct MinHeapNode* minHeapNode) {
    ++minHeap->size;
    int i = minHeap->size - 1;
    while (i && minHeapNode->freq < minHeap->array[(i - 1) / 2]->freq) {
        minHeap->array[i] = minHeap->array[(i - 1) / 2];
        i = (i - 1) / 2;
    }
    minHeap->array[i] = minHeapNode;
}

void buildMinHeap(struct MinHeap* minHeap) {
    int n = minHeap->size - 1;
    int i;
    for (i = (n - 1) / 2; i >= 0; --i)
        minHeapify(minHeap, i);
}

struct MinHeap* createAndBuildMinHeap(char data[], int freq[], int size) {
    struct MinHeap* minHeap = createMinHeap(size);
    for (int i = 0; i < size; ++i)
        minHeap->array[i] = newNode(data[i], freq[i]);
    minHeap->size = size;
    buildMinHeap(minHeap);
    return minHeap;
}

struct MinHeapNode* buildHuffmanTree(char data[], int freq[], int size) {
    struct MinHeapNode *left, *right, *top;
    struct MinHeap* minHeap = createAndBuildMinHeap(data, freq, size);

    while (!isSizeOne(minHeap)) {
        left = extractMin(minHeap);
        right = extractMin(minHeap);
        top = newNode('$', left->freq + right->freq);
        top->left = left;
        top->right = right;
        insertMinHeap(minHeap, top);
    }
    return extractMin(minHeap);
}

int isLeaf(struct MinHeapNode* root) {
    return !(root->left) && !(root->right);
}

// Decodes Huffman stream from 'in' and writes to 'out'
void huffman_decode_stream(FILE *in, FILE *out) {
    unsigned long totalCharCount;
    if (fread(&totalCharCount, sizeof(unsigned long), 1, in) != 1) return;

    unsigned char uniqueCount;
    fread(&uniqueCount, sizeof(unsigned char), 1, in);

    int size = (int)uniqueCount;
    if (size == 0 && totalCharCount > 0) size = 256; 

    char data[256];
    int freqs[256];
    
    for (int i = 0; i < size; i++) {
        fread(&data[i], sizeof(char), 1, in);
        fread(&freqs[i], sizeof(int), 1, in);
    }

    struct MinHeapNode* root = buildHuffmanTree(data, freqs, size);
    struct MinHeapNode* curr = root;
    int c;
    unsigned long extractedChars = 0;
    unsigned char buffer;

    while ((c = fgetc(in)) != EOF && extractedChars < totalCharCount) {
        buffer = (unsigned char)c;
        for (int i = 0; i < 8; i++) {
            if (extractedChars >= totalCharCount) break;

            int bit = (buffer >> (7 - i)) & 1;
            if (bit == 0)
                curr = curr->left;
            else
                curr = curr->right;

            if (isLeaf(curr)) {
                fputc(curr->data, out);
                extractedChars++;
                curr = root;
            }
        }
    }
}

// --- LZW Decoding ---

typedef struct {
    int prefix_code;
    char character;
} DecEntry;

DecEntry dict[LZW_DICT_SIZE];
int dec_next_code = 256;

void dec_init_dictionary() {
    for (int i = 0; i < 256; i++) {
        dict[i].prefix_code = -1;
        dict[i].character = (char)i;
    }
    dec_next_code = 256;
}

void output_string(FILE *out, int code) {
    if (code == -1) return;
    if (code < 256) {
        fputc((char)code, out);
    } else {
        if (dict[code].prefix_code != -1) {
            output_string(out, dict[code].prefix_code);
            fputc(dict[code].character, out);
        }
    }
}

char get_first_char(int code) {
    while (code >= 256) {
        code = dict[code].prefix_code;
    }
    return (char)code;
}

void lzw_decode_stream(FILE *in, FILE *out) {
    dec_init_dictionary();
    int old_code;
    int new_code;
    
    if (fread(&old_code, sizeof(short), 1, in) != 1) return;
    output_string(out, old_code);

    while (fread(&new_code, sizeof(short), 1, in) == 1) {
        int code_to_output = new_code;
        int char_to_add;

        if (new_code >= dec_next_code) {
             if (new_code == dec_next_code) {
                 code_to_output = old_code;
             } else {
                 // Corruption
                 break; 
             }
        }
        
        // Temporarily output logic needed here to get first char
        // Actually, just get first char of what we WILL output
        if (new_code >= dec_next_code) {
             char_to_add = get_first_char(old_code);
        } else {
             char_to_add = get_first_char(new_code);
        }

        // Logic fix:
        // if code is in dict: output entry(code). add entry(old) + first(code)
        // if code not in dict: output entry(old) + first(old). add entry(old) + first(old)
        
        if (new_code >= dec_next_code) {
            output_string(out, old_code);
            fputc((char)char_to_add, out);
        } else {
            output_string(out, new_code);
        }
        
        if (dec_next_code < LZW_DICT_SIZE) {
            dict[dec_next_code].prefix_code = old_code;
            dict[dec_next_code].character = (char)char_to_add;
            dec_next_code++;
        }
        old_code = new_code;
    }
}


int main(int argc, char* argv[]) {
    if (argc < 3) {
        printf("Usage: %s <input_file> <output_file>\n", argv[0]);
        return 1;
    }

    FILE *in = fopen(argv[1], "rb");
    if (!in) {
        perror("Error opening input");
        return 1;
    }

    // Read Flag
    int flag = fgetc(in);
    if (flag == EOF) return 0; // Empty
    
    printf("Mode Detected: %s\n", flag ? "LZW+Huffman" : "Huffman Only");

    // We ALWAYS Huffman Decompress first.
    // If Flag == 1: LZW+Huffman -> so huffman decodes to TEMP (LZW bin), then LZW decodes to OUTPUT.
    // If Flag == 0: Huffman Only -> so huffman decodes directly to OUTPUT.

    const char *tempFile = "temp_decoded.bin";
    const char *finalOutput = argv[2];

    if (flag == 1) {
        // Pipeline: In -> Huffman -> Temp -> LZW -> Out
        FILE *temp = fopen(tempFile, "wb");
        if (!temp) return 1;
        
        huffman_decode_stream(in, temp);
        fclose(temp);
        
        // Phase 2
        FILE *lzwSource = fopen(tempFile, "rb");
        FILE *finalOut = fopen(finalOutput, "wb");
        lzw_decode_stream(lzwSource, finalOut);
        
        fclose(lzwSource);
        fclose(finalOut);
        remove(tempFile);
    } else {
        // Pipeline: In -> Huffman -> Out
        FILE *out = fopen(finalOutput, "wb");
        huffman_decode_stream(in, out);
        fclose(out);
    }

    fclose(in);
    printf("Decompression Complete.\n");
    return 0;
}
