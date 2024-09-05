import os
import zipfile
import subprocess
from flask import Flask, request, render_template, redirect, url_for, flash
import difflib


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.secret_key = 'supersecretkey'
def run_python_file(filepath, input_data):
    """Execute a Python file with input and return its output."""
    try:
        result = subprocess.run(
            ['python3', filepath],
            input=input_data,
            text=True,
            capture_output=True,
            timeout=5
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return 'Timeout'



# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_zip():
    if 'file' not in request.files or 'input_data' not in request.form or 'expected_output' not in request.form:
        flash('Missing file or input/output data')
        return redirect(request.url)

    file = request.files['file']
    input_data = request.form['input_data']
    expected_output = request.form['expected_output']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and file.filename.endswith('.zip'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        flash('File successfully uploaded')

        # Extract the zip file
        extracted_folder = extract_zip(filepath)

        # Split the input and expected output based on the delimiter (e.g., "---")
        input_cases = input_data.split('---')
        expected_outputs = expected_output.split('---')

        # Check if we have the same number of inputs and expected outputs
        if len(input_cases) != len(expected_outputs):
            flash("Number of inputs doesn't match number of expected outputs")
            return redirect(url_for('index'))

        # Grade files using the test cases
        grade_results = grade_files(extracted_folder, input_cases, expected_outputs)
        return render_template('result.html', results=grade_results)

    flash('Invalid file format, please upload a zip file.')
    return redirect(url_for('index'))

def grade_files(folder, input_cases, expected_outputs):
    """Grade each Python file by running it with multiple test cases and comparing its output with the expected outputs."""
    results = []

    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.py') and not file.startswith('._'):
                # Path to the current Python file
                filepath = os.path.join(root, file)
                file_results = []

                # Loop through each test case
                for input_data, expected_output in zip(input_cases, expected_outputs):
                    # Run the Python file with the given input
                    output = run_python_file(filepath, input_data.strip())

                    # Compare the output with the expected output
                    if output.strip() == expected_output.strip():
                        file_results.append("Pass")
                    else:
                        file_results.append(f"Fail (Expected: {expected_output.strip()}, Got: {output.strip()})")

                # Store the result for this file
                results.append((file, file_results))

    return results

def extract_zip(filepath):
    # Extract zip to a folder
    folder_name = os.path.splitext(os.path.basename(filepath))[0]
    extract_dir = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    with zipfile.ZipFile(filepath, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    return extract_dir

if __name__ == '__main__':
    app.run(debug=True)
