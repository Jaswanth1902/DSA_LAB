#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MAX_TREE_HT 100
#define LZW_DICT_SIZE 4096

// --- LZW Functions ---

typedef struct DictionaryEntry {
    int prefix_code;
    char character;
    int code;
    struct DictionaryEntry *next;
} DictionaryEntry;

DictionaryEntry* dictionary[LZW_DICT_SIZE];
int next_code = 256;

void init_dictionary() {
    for (int i = 0; i < LZW_DICT_SIZE; i++) {
        dictionary[i] = NULL;
    }
    next_code = 256;
}

unsigned int hash_func(int prefix_code, unsigned char character) {
    return ((prefix_code << 8) ^ character) % LZW_DICT_SIZE;
}

void insert_dictionary(int prefix_code, unsigned char character, int code) {
    unsigned int index = hash_func(prefix_code, character);
    DictionaryEntry *new_entry = (DictionaryEntry*)malloc(sizeof(DictionaryEntry));
    new_entry->prefix_code = prefix_code;
    new_entry->character = (char)character;
    new_entry->code = code;
    new_entry->next = dictionary[index];
    dictionary[index] = new_entry;
}

int search_dictionary(int prefix_code, unsigned char character) {
    unsigned int index = hash_func(prefix_code, character);
    DictionaryEntry *curr = dictionary[index];
    while (curr != NULL) {
        if (curr->prefix_code == prefix_code && (unsigned char)curr->character == character) {
            return curr->code;
        }
        curr = curr->next;
    }
    return -1;
}

void free_dictionary() {
    for (int i = 0; i < LZW_DICT_SIZE; i++) {
        DictionaryEntry *curr = dictionary[i];
        while (curr) {
            DictionaryEntry *temp = curr;
            curr = curr->next;
            free(temp);
        }
        dictionary[i] = NULL;
    }
}

void lzw_compress_file(const char* inputFile, const char* tempFile) {
    FILE *in = fopen(inputFile, "rb");
    FILE *out = fopen(tempFile, "wb");
    if (!in || !out) return;

    init_dictionary();
    int prefix_code = -1;
    int c;
    
    if ((c = fgetc(in)) != EOF) {
        prefix_code = c;
    }

    while ((c = fgetc(in)) != EOF) {
        int index = search_dictionary(prefix_code, (unsigned char)c);
        if (index != -1) {
            prefix_code = index;
        } else {
            fwrite(&prefix_code, sizeof(short), 1, out);
            if (next_code < LZW_DICT_SIZE) {
                insert_dictionary(prefix_code, (unsigned char)c, next_code++);
            }
            prefix_code = c;
        }
    }

    if (prefix_code != -1) {
        fwrite(&prefix_code, sizeof(short), 1, out);
    }

    fclose(in);
    fclose(out);
    free_dictionary();
}

// --- Huffman Functions ---

struct MinHeapNode {
    char data;
    unsigned freq;
    struct MinHeapNode *left, *right;
};

struct MinHeap {
    unsigned size;
    unsigned capacity;
    struct MinHeapNode** array;
};

struct MinHeapNode* newNode(char data, unsigned freq) {
    struct MinHeapNode* temp = (struct MinHeapNode*)malloc(sizeof(struct MinHeapNode));
    temp->left = temp->right = NULL;
    temp->data = data;
    temp->freq = freq;
    return temp;
}

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

struct MinHeapNode* buildHuffmanTree(char data[], int freq[], int size) {
    struct MinHeapNode *left, *right, *top;
    struct MinHeap* minHeap = createMinHeap(size);
    for (int i = 0; i < size; ++i)
        minHeap->array[i] = newNode(data[i], freq[i]);
    minHeap->size = size;
    buildMinHeap(minHeap);

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

void getCodes(struct MinHeapNode* root, int arr[], int top, char* codes[]) {
    if (root->left) {
        arr[top] = 0;
        getCodes(root->left, arr, top + 1, codes);
    }
    if (root->right) {
        arr[top] = 1;
        getCodes(root->right, arr, top + 1, codes);
    }
    if (!(root->left) && !(root->right)) {
        codes[(unsigned char)root->data] = (char*)malloc(top + 1);
        for(int i=0; i<top; ++i) {
            codes[(unsigned char)root->data][i] = arr[i] + '0';
        }
        codes[(unsigned char)root->data][top] = '\0';
    }
}

void writeBit(FILE *out, int bit, unsigned char *buffer, int *bitCount) {
    if (bit) {
        *buffer |= (1 << (7 - *bitCount));
    }
    (*bitCount)++;
    if (*bitCount == 8) {
        fputc(*buffer, out);
        *buffer = 0;
        *bitCount = 0;
    }
}

// Rewritten to take open file pointers
void huffman_encode_stream(FILE *in, FILE *out) {
    int freq[256] = {0};
    int c;
    unsigned long totalCharCount = 0;
    
    // Pass 1: Count Freq
    while ((c = fgetc(in)) != EOF) {
        freq[c]++;
        totalCharCount++;
    }
    
    char data[256];
    int freqs[256];
    int size = 0;
    for (int i = 0; i < 256; i++) {
        if (freq[i] > 0) {
            data[size] = (char)i;
            freqs[size] = freq[i];
            size++;
        }
    }

    if (size == 0) {
         unsigned long zero = 0;
         unsigned char zeroChar = 0;
         fwrite(&zero, sizeof(unsigned long), 1, out);
         fwrite(&zeroChar, sizeof(unsigned char), 1, out);
         return;
    }

    struct MinHeapNode* root = buildHuffmanTree(data, freqs, size);
    
    char* codes[256] = {0};
    int arr[MAX_TREE_HT], top = 0;
    getCodes(root, arr, top, codes);

    // Write Header
    fwrite(&totalCharCount, sizeof(unsigned long), 1, out); 
    unsigned char uniqueCount = (unsigned char)size;
    fwrite(&uniqueCount, sizeof(unsigned char), 1, out);

    for (int i = 0; i < size; i++) {
        fwrite(&data[i], sizeof(char), 1, out);
        fwrite(&freqs[i], sizeof(int), 1, out);
    }

    // Write Data
    rewind(in);
    unsigned char buffer = 0;
    int bitCount = 0;
    while ((c = fgetc(in)) != EOF) {
        char *code = codes[(unsigned char)c];
        for (int i = 0; code[i] != '\0'; i++) {
            writeBit(out, code[i] - '0', &buffer, &bitCount);
        }
    }
    if (bitCount > 0) {
        fputc(buffer, out);
    }
}

long get_file_size(const char *filename) {
    FILE *f = fopen(filename, "rb");
    if (!f) return 0;
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fclose(f);
    return size;
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        printf("Usage: %s <input_file> <output_file>\n", argv[0]);
        return 1;
    }

    const char* inputFile = argv[1];
    const char* outputFile = argv[2];
    const char* tempLzwFile = "temp_lzw_output.bin";

    // 1. Calculate Original Size
    long originalSize = get_file_size(inputFile);

    // 2. Perform LZW Compression to Temp
    lzw_compress_file(inputFile, tempLzwFile);
    long lzwSize = get_file_size(tempLzwFile);

    // 3. Decide Mode
    // If LZW increased size or didn't help much, use Raw Huffman.
    // LZW overhead is 2x. If LZW size >= Original, definitely skip.
    // We'll trust LZW only if it shrinks.
    int use_lzw = (lzwSize < originalSize);

    printf("Original Size: %ld, LZW Size: %ld. Decision: %s\n", 
           originalSize, lzwSize, use_lzw ? "LZW+Huffman" : "Huffman Only");

    // 4. Open Output and Write Flag
    FILE *out = fopen(outputFile, "wb");
    if (!out) {
        perror("Error opening output");
        return 1;
    }
    
    fputc(use_lzw ? 1 : 0, out); // Write Flag Byte

    // 5. Open Source for Huffman
    const char *huffmanSource = use_lzw ? tempLzwFile : inputFile;
    FILE *in = fopen(huffmanSource, "rb");
    
    if (in) {
        huffman_encode_stream(in, out);
        fclose(in);
    }

    fclose(out);
    remove(tempLzwFile);

    printf("Compression Complete.\n");
    return 0;
}
