import os
import json
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import compress
import decompress

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
STATS_FILE = 'stats.json'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {'compressed': 0, 'decompressed': 0}
    try:
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'compressed': 0, 'decompressed': 0}

def save_stats(stats):
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f)

def update_stats(mode):
    stats = load_stats()
    if mode == 'compress':
        stats['compressed'] = stats.get('compressed', 0) + 1
    elif mode == 'decompress':
        stats['decompressed'] = stats.get('decompressed', 0) + 1
    save_stats(stats)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stats')
def get_stats():
    return jsonify(load_stats())

@app.route('/reset_stats', methods=['POST'])
def reset_stats():
    if os.path.exists(STATS_FILE):
        os.remove(STATS_FILE)
    return jsonify({'status': 'success', 'compressed': 0, 'decompressed': 0})


@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    mode = request.form.get('mode')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file:
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        
        original_size = os.path.getsize(input_path)
        tree_data = None
        
        if mode == 'compress':
            try:
                # Get Tree Data here
                base_name = os.path.splitext(filename)[0] + '.lzh'
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], base_name)
                tree_data = compress.compress_file(input_path, output_path)
                update_stats('compress')
                
                output_filename = base_name
            except Exception as e:
                return jsonify({'error': str(e)})
                
        elif mode == 'decompress':
            # ... existing decompress logic ...
            output_filename = filename + '.restored'
            if filename.endswith('.lzh') or filename.endswith('.bin'):
                 output_filename = os.path.splitext(filename)[0]
            
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            try:
                decompress.decompress_file(input_path, output_path)
                update_stats('decompress')
            except Exception as e:
                 return jsonify({'error': str(e)})
            
            # For consistency, return empty debug info on decompress for now
            # debug_info = {"original_preview": "", "compressed_preview": ""} 
        
        else:
            return jsonify({'error': 'Invalid mode'})

        if not os.path.exists(output_path):
             return jsonify({'error': 'Processing failed to create output file'})

        processed_size = os.path.getsize(output_path)
        
        # Determine if it was Identity Mode
        is_identity = (processed_size == original_size + 1)
        
        return jsonify({
            'original_size': original_size,
            'processed_size': processed_size,
            'filename': output_filename,
            'download_url': f'/download/{output_filename}',
            'tree_data': tree_data,
            'is_identity': is_identity
        })

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

@app.route('/simulator')
def simulator():
    return render_template('simulator.html')

@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    data = request.json
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    results = compress.simulate_all(text)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
