from flask import Flask, request, jsonify
import hashlib
import threading

app = Flask(__name__)

def intensive_sort(values):
    return sorted(values)

@app.route('/compute', methods=['POST'])
def compute():
    data = request.json
    sorted_values = intensive_sort(data['values'])
    return jsonify({'sorted': sorted_values})

@app.route('/hash', methods=['POST'])
def hash_input():
    data = request.json
    sha256_hash = hashlib.sha256(data['input'].encode()).hexdigest()
    return jsonify({'sha256': sha256_hash})

@app.route('/health', methods=['GET'])
def health():
    return '', 200

if __name__ == '__main__':
    app.run(port=8005)