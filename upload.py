import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Access Pinata API credentials from environment variables
PINATA_API_KEY = os.getenv('PINATA_API_KEY')
PINATA_SECRET_API_KEY = os.getenv('PINATA_SECRET_API_KEY')

# Folder to temporarily store the uploaded file before sending to Pinata
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def serve_index():
    # Serve the index.html from the static folder
    return send_from_directory('static', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_to_ipfs():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected for uploading'}), 400

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            # Upload file to Pinata
            with open(file_path, 'rb') as fp:
                response = requests.post(
                    url='https://api.pinata.cloud/pinning/pinFileToIPFS',
                    files={'file': (filename, fp)},
                    headers={
                        'pinata_api_key': PINATA_API_KEY,
                        'pinata_secret_api_key': PINATA_SECRET_API_KEY
                    }
                )

            if response.status_code == 200:
                ipfs_hash = response.json()['IpfsHash']
                return jsonify({'success': True, 'hash': ipfs_hash}), 200
            else:
                return jsonify({'success': False, 'message': 'Failed to upload to Pinata'}), 500
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            # Clean up: Remove the file after uploading
            if os.path.exists(file_path):
                os.remove(file_path)

if __name__ == '__main__':
    app.run(debug=True,)
