from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
import base64
from ml import extract_text
from pathlib import Path

# Initialize Flask app
app = Flask(__name__, 
           template_folder='app/templates',
           static_folder='app/static')

# Set upload folder in user's home directory
HOME_DIR = str(Path.home())
UPLOAD_FOLDER = os.path.join(HOME_DIR, 'image_to_text_uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    print(f"Upload directory created/verified at: {app.config['UPLOAD_FOLDER']}")
except Exception as e:
    print(f"Error creating upload directory: {e}")
    # Fallback to /tmp directory if home directory is not accessible
    app.config['UPLOAD_FOLDER'] = '/tmp/image_to_text_uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    print(f"Using fallback upload directory: {app.config['UPLOAD_FOLDER']}")

# MongoDB Atlas connection
try:
    client = MongoClient('mongodb+srv://nguyentruc766:nct067203@ocr.5xegf.mongodb.net/?tlsAllowInvalidCertificates=true')
    db = client['image_to_text_db']
    history_collection = db['conversion_history']
    print("Connected to MongoDB Atlas successfully!")
except Exception as e:
    print(f"Error connecting to MongoDB Atlas: {e}")

def save_to_history(image_path, extracted_text):
    try:
        # Read the image file and convert to base64
        with open(image_path, 'rb') as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Create history document
        history_item = {
            'image_data': encoded_image,
            'text': extracted_text,
            'date': datetime.now(),
            'filename': os.path.basename(image_path)
        }

        # Insert into MongoDB
        history_collection.insert_one(history_item)
        return True
    except Exception as e:
        print(f"Error saving to history: {e}")
        return False

@app.route('/')
def index():
    try:
        # Fetch conversion history from MongoDB
        history = list(history_collection.find().sort('date', -1).limit(10))
        
        # Process the history items for display
        for item in history:
            item['image_url'] = f"data:image/jpeg;base64,{item['image_data']}"
            item['date'] = item['date'].strftime('%d/%m/%Y %H:%M')
            # Convert ObjectId to string for JSON serialization
            item['_id'] = str(item['_id'])
            
        return render_template('index.html', history=history)
    except Exception as e:
        print(f"Error fetching history: {e}")
        return render_template('index.html', history=[])

@app.route('/', methods=['POST'])
def upload_file():
    try:
        if 'image_upload' not in request.files:
            return render_template('index.html', error='No file uploaded')

        file = request.files['image_upload']
        if file.filename == '':
            return render_template('index.html', error='No file selected')

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
        if not '.' in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return render_template('index.html', error='Invalid file type. Please upload an image file.')

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
            
            # Extract text from image
            text = extract_text(filepath)
            
            # Save to history
            if not save_to_history(filepath, text):
                raise Exception("Failed to save to history")

            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)

            # Get updated history
            history = list(history_collection.find().sort('date', -1).limit(10))
            for item in history:
                item['image_url'] = f"data:image/jpeg;base64,{item['image_data']}"
                item['date'] = item['date'].strftime('%d/%m/%Y %H:%M')
                item['_id'] = str(item['_id'])

            return render_template('index.html', text=text.split('\n'), history=history)
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            error_message = str(e)
            if "tesseract" in error_message.lower():
                error_message = "Error processing image: Could not extract text. Please ensure the image contains clear text."
            return render_template('index.html', error=error_message)
            
    except Exception as e:
        return render_template('index.html', error=f'An unexpected error occurred: {str(e)}')

@app.route('/history')
def get_history():
    try:
        history = list(history_collection.find().sort('date', -1).limit(10))
        for item in history:
            item['image_url'] = f"data:image/jpeg;base64,{item['image_data']}"
            item['date'] = item['date'].strftime('%d/%m/%Y %H:%M')
            item['_id'] = str(item['_id'])
        return jsonify(history)
    except Exception as e:
        print(f"Error fetching history: {e}")
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)