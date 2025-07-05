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
    # This route displays an image (either original or previously processed) and options to process it further.
    # `filename` here can be an original filename or a processed filename.
    # We need to determine if it's from UPLOAD_FOLDER or PROCESSED_FOLDER.

    original_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    processed_image_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)

    is_processed_image = os.path.exists(processed_image_path)

    image_url = ""
    source_folder_for_display = ""

    if is_processed_image:
        image_url = url_for('display_processed_file', filename=filename)
        source_folder_for_display = app.config['PROCESSED_FOLDER']
    elif os.path.exists(original_image_path):
        image_url = url_for('display_uploaded_file', filename=filename)
        source_folder_for_display = app.config['UPLOAD_FOLDER']
    else:
        flash(f"Image {filename} not found.")
        return redirect(url_for('index'))

    # `current_filename_for_processing` is the image that will be processed next.
    # `display_image_url` is the URL of the image shown on the page.
    # `original_uploaded_filename` tracks the very first image for reference if needed.

    # If `filename` is already processed, it might look like "enhanced_original.jpg".
    # We need a way to trace back to the actual original upload if necessary,
    # but for chaining, `filename` IS the current source.

    return render_template('edit.html',
                           current_filename_for_processing=filename,
                           display_image_url=image_url,
                           is_processed_image=is_processed_image)


@app.route('/process/enhance/<source_filename>', methods=['POST'])
def enhance_image_route(source_filename):
    try:
        # Determine if the source_filename is from UPLOAD_FOLDER or PROCESSED_FOLDER
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], source_filename)
        processed_path_as_source = os.path.join(app.config['PROCESSED_FOLDER'], source_filename)

        actual_source_path = ""
        if os.path.exists(processed_path_as_source):
            actual_source_path = processed_path_as_source
        elif os.path.exists(original_path):
            actual_source_path = original_path
        else:
            flash(f'Source image {source_filename} not found.')
            return redirect(url_for('index'))

        img = Image.open(actual_source_path)
        img_enhanced = ImageOps.autocontrast(img)

        # Create a new filename to avoid overwriting and show progression
        if source_filename.startswith("enhanced_") or source_filename.startswith("bg_removed_"):
            new_processed_filename = "enhanced_" + source_filename.split("_", 1)[1] if "_" in source_filename else "enhanced_processed_" + source_filename
        else: # Original file
            new_processed_filename = "enhanced_" + source_filename

        # Ensure unique filenames if operations are repeated (e.g. enhance_enhance_...)
        # This simple prefixing might get long. A more robust system might use IDs or checksums.
        count = 0
        temp_filename = new_processed_filename
        while os.path.exists(os.path.join(app.config['PROCESSED_FOLDER'], temp_filename)):
            count += 1
            base, ext = os.path.splitext(new_processed_filename)
            # Remove previous count if exists
            if base.endswith(f"_{count-1}"):
                 base = base[:-(len(str(count-1))+1)]
            temp_filename = f"{base}_{count}{ext}"
        new_processed_filename = temp_filename


        destination_path = os.path.join(app.config['PROCESSED_FOLDER'], new_processed_filename)
        img_enhanced.save(destination_path)

        flash('Image enhanced successfully!')
        # After processing, redirect to the edit page with the new processed filename as the current image
        return redirect(url_for('edit_image', filename=new_processed_filename))
    except Exception as e:
        flash(f'Error processing image: {e}')
        return redirect(url_for('edit_image', filename=source_filename))

# Placeholder for AI Background Removal (modified for chaining)
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

@app.route('/process/remove_bg/<source_filename>', methods=['POST'])
def remove_bg_route(source_filename):
    try:
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], source_filename)
        processed_path_as_source = os.path.join(app.config['PROCESSED_FOLDER'], source_filename)

        actual_source_path = ""
        if os.path.exists(processed_path_as_source):
            actual_source_path = processed_path_as_source
        elif os.path.exists(original_path):
            actual_source_path = original_path
        else:
            flash(f'Source image {source_filename} not found.')
            return redirect(url_for('index'))

        # Create a new filename
        if source_filename.startswith("enhanced_") or source_filename.startswith("bg_removed_"):
             new_processed_filename = "bg_removed_" + source_filename.split("_", 1)[1] if "_" in source_filename else "bg_removed_processed_" + source_filename
        else: # Original file
            new_processed_filename = "bg_removed_" + source_filename

        count = 0
        temp_filename = new_processed_filename
        while os.path.exists(os.path.join(app.config['PROCESSED_FOLDER'], temp_filename)):
            count += 1
            base, ext = os.path.splitext(new_processed_filename)
            if base.endswith(f"_{count-1}"):
                 base = base[:-(len(str(count-1))+1)]
            temp_filename = f"{base}_{count}{ext}"
        new_processed_filename = temp_filename

        destination_path = os.path.join(app.config['PROCESSED_FOLDER'], new_processed_filename)

        success = remove_background_ai(actual_source_path, destination_path)

        if success:
            flash('Background removal (placeholder) complete!')
            return redirect(url_for('edit_image', filename=new_processed_filename))
        else:
            flash('Error during background removal (placeholder).')
            return redirect(url_for('edit_image', filename=source_filename))

    except Exception as e:
        flash(f'Error in background removal route: {e}')
        return redirect(url_for('edit_image', filename=source_filename))

# Removed edit_image_result as its functionality is merged into edit_image
# The edit_image route now handles displaying either original or processed images
# and serves as the single point for further edits.

if __name__ == '__main__':
    for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    app.run(debug=True)
