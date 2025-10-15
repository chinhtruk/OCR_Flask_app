# Important imports
from app import app
from flask import request, render_template, url_for
import os


# Always use secure_filename from werkzeug.utils to sanitize file names
# before saving them to the server. {chatGPT recommendation lol}
from werkzeug.utils import secure_filename


import numpy as np
from PIL import Image
import random
import string
import pytesseract
from ml import extract_text

# Adding path to config
app.config['INITIAL_FILE_UPLOADS'] = 'app/static/uploads'

# Route to home page
@app.route("/", methods=["GET", "POST"])
def index():
    full_filename = url_for('static', filename='images/white_bg.jpg')

    if request.method == "POST":
        image_upload = request.files['image_upload']
        if image_upload:
            # Save the file
            filename = secure_filename(image_upload.filename)
            filepath = os.path.join(app.config['INITIAL_FILE_UPLOADS'], filename)
            image_upload.save(filepath)

            # Extract text from the saved image
            extracted_text = extract_text(filepath)
            img_url = url_for('static', filename='uploads/' + filename)

            # Return template with text and image displayed
            return render_template('index.html', img_url=img_url, full_filename=filepath, text=extracted_text)

    # Default GET request processing
    return render_template("index.html", full_filename=full_filename)

# Main function
if __name__ == '__main__':
    app.run(debug=True)


