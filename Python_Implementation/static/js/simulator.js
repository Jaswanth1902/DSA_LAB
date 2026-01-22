document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('simulatorInput');
    const charCount = document.getElementById('charCount');
    const clearBtn = document.getElementById('clearBtn');
    const sampleBtn = document.getElementById('sampleBtn');

    // UI Elements
    const lzwDictBody = document.getElementById('lzwDictBody');
    const treeContainer = document.getElementById('huffmanTreeContainer');

    // Tabs
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.style.display = 'none');
            btn.classList.add('active');
            document.getElementById(tabId + 'Tab').style.display = 'block';
        });
    });

    // Sample Text
    const sampleText = "The transition to a digital-first economy has accelerated the demand for intelligent data compression techniques. Hybrid algorithms, such as LZW combined with Huffman coding, offer a powerful solution by leveraging both dictionary-based and statistical redundancies. This simulator allows you to explore how different data patterns respond to these classic yet effective algorithms in real-time.";

    // Debounce function
    let timeout = null;
    input.addEventListener('input', () => {
        clearTimeout(timeout);
        charCount.innerText = `${new Blob([input.value]).size} bytes`;
        timeout = setTimeout(simulate, 300);
    });

    clearBtn.addEventListener('click', () => {
        input.value = '';
        charCount.innerText = '0 bytes';
        resetUI();
    });

    sampleBtn.addEventListener('click', () => {
        input.value = sampleText;
        charCount.innerText = `${new Blob([input.value]).size} bytes`;
        simulate();
    });

    async function simulate() {
        const text = input.value;
        if (!text) {
            resetUI();
            return;
        }

        try {
            const response = await fetch('/api/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });

            const data = await response.json();
            if (data.error) throw new Error(data.error);

            updateUI(data);
        } catch (err) {
            console.error('Simulation failed:', err);
        }
    }

    function updateUI(data) {
        // Update Huffman Tree
        renderHuffmanTree(data.huffman_tree);

        // Update LZW Dictionary
        renderLZWDict(data.lzw_dict);
    }


    function renderHuffmanTree(treeData) {
        treeContainer.innerHTML = '';
        if (!treeData) return;

        const width = treeContainer.offsetWidth || 600;
        const height = 400;

        const svg = d3.select("#huffmanTreeContainer")
            .append("svg")
            .attr("width", "100%")
            .attr("height", height)
            .append("g")
            .attr("transform", "translate(40,40)");

        const tree = d3.tree().size([width - 80, height - 80]);
        const root = d3.hierarchy(treeData);
        tree(root);

        // Links
        svg.selectAll(".link")
            .data(root.links())
            .enter().append("path")
            .attr("class", "link")
            .attr("d", d3.linkVertical().x(d => d.x).y(d => d.y));

        // Nodes
        const node = svg.selectAll(".node")
            .data(root.descendants())
            .enter().append("g")
            .attr("class", "node")
            .attr("transform", d => `translate(${d.x},${d.y})`);

        node.append("circle").attr("r", 15)
            .append("title").text(d => `Freq: ${d.data.value}`);

        node.append("text")
            .attr("dy", ".35em")
            .attr("text-anchor", "middle")
            .text(d => d.data.name || '');
    }

    function renderLZWDict(dict) {
        lzwDictBody.innerHTML = '';
        if (!dict) return;

        // Sort by code (value) to show chronological order of addition
        const items = Object.entries(dict).sort((a, b) => a[1] - b[1]);

        items.forEach(([key, val]) => {
            const row = document.createElement('tr');
            
            // Format key tuple (prefix, char)
            const cleanKey = key.replace(/[()]/g, '').split(',').map(s => s.trim()).join(' + ');
            
            row.innerHTML = `
                <td style="padding: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.05); color: #f1f5f9;">${cleanKey}</td>
                <td style="padding: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: right; color: var(--accent);">${val}</td>
            `;
            lzwDictBody.appendChild(row);
        });
    }

    function resetUI() {
        lzwDictBody.innerHTML = '';
        treeContainer.innerHTML = '';
    }
});
