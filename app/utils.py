import os
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, subdir=''):
    """
    Saves a file securely to the uploads folder within an optional subdirectory.
    Returns the relative file_path to be stored in the DB.
    """
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create subdirectories if needed (e.g. documents/ or prescriptions/)
        target_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subdir)
        os.makedirs(target_dir, exist_ok=True)
        
        file_path = os.path.join(target_dir, filename)
        file.save(file_path)
        
        # Return path relative to uploads/ for DB
        return os.path.join(subdir, filename).replace('\\', '/')
    return None
