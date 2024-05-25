from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'bin'}
UPDATE_FLAG_FILE = 'update_flag.txt'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    os.chmod(UPLOAD_FOLDER, 0o755)  # Set directory permissions

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'firmwareFile' not in request.files:
        return render_template('index.html', error='No file part in request.files')
    file = request.files['firmwareFile']
    if file.filename == '':
        return render_template('index.html', error='No selected file')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        os.chmod(file_path, 0o644)  # Set file permissions
        with open(UPDATE_FLAG_FILE, 'w') as f:
            f.write(filename)
        os.chmod(UPDATE_FLAG_FILE, 0o644)  # Set file permissions
        return redirect(url_for('trigger_update'))
    return render_template('index.html', error='Invalid file format. Only .bin files are allowed.')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/check_for_update')
def check_for_update():
    if os.path.exists(UPDATE_FLAG_FILE):
        with open(UPDATE_FLAG_FILE, 'r') as f:
            filename = f.read().strip()
        return jsonify({"update": True, "filename": filename})
    else:
        return jsonify({"update": False})

@app.route('/trigger_update')
def trigger_update():
    if os.path.exists(UPDATE_FLAG_FILE):
        with open(UPDATE_FLAG_FILE, 'r') as f:
            filename = f.read().strip()
        return render_template('trigger_update.html', filename=filename)
    else:
        return redirect(url_for('index'))

@app.route('/trigger_update_action', methods=['POST'])
def trigger_update_action():
    filename = request.form.get('filename')
    if filename and allowed_file(filename):
        with open(UPDATE_FLAG_FILE, 'w') as f:
            f.write(filename)
        os.chmod(UPDATE_FLAG_FILE, 0o644)  # Set file permissions
        # Trigger the ESP32 to check for updates
        return render_template('update_result.html', result='Update initiated.')
    return render_template('trigger_update.html', error='Invalid file format. Only .bin files are allowed.')

@app.route('/reset', methods=['POST'])
def reset():
    # Remove the update flag file
    if os.path.exists(UPDATE_FLAG_FILE):
        os.remove(UPDATE_FLAG_FILE)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
