from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed' # To store processed images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['SECRET_KEY'] = 'supersecretkey' # Needed for flash messages

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'imageUpload' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['imageUpload']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        flash(f'File {filename} successfully uploaded. Ready for processing.')
        # Redirect to a new route that shows the uploaded image and processing options
        return redirect(url_for('edit_image', filename=filename))
    else:
        flash('Allowed image types are -> png, jpg, jpeg, gif')
        return redirect(request.url)

@app.route('/uploads/<filename>')
def display_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/processed/<filename>')
def display_processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

@app.route('/edit/<filename>')
def edit_image(filename):
    # This route will display the uploaded image and options to process it
    uploaded_image_url = url_for('display_uploaded_file', filename=filename)
    return render_template('edit.html', filename=filename, uploaded_image_url=uploaded_image_url)

@app.route('/process/enhance/<filename>', methods=['POST'])
def enhance_image_route(filename):
    try:
        source_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(source_path):
            flash('Original image not found.')
            return redirect(url_for('index'))

        img = Image.open(source_path)

        # Example: Auto-contrast
        img_enhanced = ImageOps.autocontrast(img)

        processed_filename = "enhanced_" + filename
        destination_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
        img_enhanced.save(destination_path)

        flash('Image enhanced successfully!')
        # Show the edit page again, but now with the processed image
        return redirect(url_for('edit_image_result', original_filename=filename, processed_filename=processed_filename))
    except Exception as e:
        flash(f'Error processing image: {e}')
        return redirect(url_for('edit_image', filename=filename))

# Placeholder for AI Background Removal
def remove_background_ai(image_path, output_path):
    """
    Placeholder function for AI background removal.
    In a real implementation, this would call U-2-Net or an API like remove.bg.
    For now, it just copies the image to simulate a change.
    """
    try:
        img = Image.open(image_path)
        # Simulate processing by converting to grayscale (or any simple operation)
        # In reality, this would be a complex AI model call.
        # For demonstration, let's just save a copy or a slightly modified version.
        # If using remove.bg API, you'd make an HTTP request here.
        # If using a local model (U-2-Net), you'd load the model and process the image.
        img.save(output_path) # Just saving a copy for placeholder
        return True
    except Exception as e:
        print(f"Error in remove_background_ai: {e}")
        return False

@app.route('/process/remove_bg/<filename>', methods=['POST'])
def remove_bg_route(filename):
    try:
        source_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(source_path):
            flash('Original image not found.')
            return redirect(url_for('index'))

        processed_filename = "bg_removed_" + filename
        destination_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)

        success = remove_background_ai(source_path, destination_path) # Call placeholder

        if success:
            flash('Background removal (placeholder) complete!')
            return redirect(url_for('edit_image_result', original_filename=filename, processed_filename=processed_filename))
        else:
            flash('Error during background removal (placeholder).')
            return redirect(url_for('edit_image', filename=filename))

    except Exception as e:
        flash(f'Error in background removal route: {e}')
        return redirect(url_for('edit_image', filename=filename))

@app.route('/edit_result/<original_filename>/<processed_filename>')
def edit_image_result(original_filename, processed_filename):
    original_image_url = url_for('display_uploaded_file', filename=original_filename)
    processed_image_url = url_for('display_processed_file', filename=processed_filename)
    return render_template('edit.html',
                           filename=original_filename, # Keep original filename for context
                           uploaded_image_url=original_image_url,
                           processed_image_url=processed_image_url,
                           processed_filename=processed_filename)


if __name__ == '__main__':
    for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    app.run(debug=True)
