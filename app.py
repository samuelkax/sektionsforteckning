from flask import Flask, render_template, request, send_file, redirect, url_for, Response, flash
import os
import csv
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flashing messages
app.config['UPLOAD_FOLDER'] = 'processed_files'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
app.config['INVALID_TYPES_FILE'] = 'invalid_types.txt'  # Path to the file containing invalid types

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Function to read invalid types from a text file
def read_invalid_types(file_path):
    invalid_types = set()
    with open(file_path, 'r', encoding='latin-1') as f:
        for line in f:
            invalid_types.add(line.strip())
    return invalid_types

# Function to process CSV data and return as a list of rows
def process_csv(file_content, invalid_types):
    processed_output = io.StringIO()
    writer = csv.writer(processed_output, delimiter=';')
    
    # Initialize dictionary for grouping by zone
    zone_dict = {}
    
    # Read the CSV file from file_content
    file_stream = io.StringIO(file_content.decode('latin-1'))  # Read file content using latin-1 encoding
    reader = csv.reader(file_stream, delimiter=';')
    
    # Read and check the third row (after reading the first two rows)
    next(reader, None)  # Read and ignore the first row (header)
    next(reader, None)  # Read and ignore the second row
    third_row = next(reader, None)  # Read the third row for checking
    if third_row and third_row[0] != "Rapport konfiguration":
        # Print the third row for debugging purposes
        print(f"Third row found: {third_row}")
        
        # Return an error message including the third row content
        return None, f"Error: The third row does not contain 'Rapport konfiguration'. Found: {third_row}"
    
    # Skip rows 4 through 12
    for _ in range(9):
        next(reader, None)
    
    # Begin processing from the 13th row onwards
    for row in reader:
        if len(row) < 3:
            continue  # Skip rows that don't have enough columns
        zone = row[1].strip('"')
        address = row[2].strip('"')
        device_type = row[3].strip('"')
        
        # Check if device type is in the invalid types list
        if device_type not in invalid_types:
            if zone not in zone_dict:
                zone_dict[zone] = []
            zone_dict[zone].append(address)
    
    # Collect the processed data into a list of rows
    processed_rows = []
    for zone, addresses in zone_dict.items():
        if len(addresses) == 1:
            processed_rows.append([zone, addresses[0]])
        else:
            addresses.sort()
            ranges = shorten_address_list(addresses)
            processed_rows.append([zone, ", ".join(ranges)])
    
    # Write processed rows to the output CSV
    for row in processed_rows:
        writer.writerow(row)
    
    return processed_rows, processed_output.getvalue()

# Function to shorten the list of addresses
def shorten_address_list(addresses):
    ranges = []
    start = end = addresses[0]
    
    for address in addresses[1:]:
        if int(address.split('.')[1]) == int(end.split('.')[1]) + 1:
            end = address
        else:
            if start == end:
                ranges.append(start)
            else:
                ranges.append(f"{start}-{end}")
            start = end = address
    
    if start == end:
        ranges.append(start)
    else:
        ranges.append(f"{start}-{end}")
    
    return ranges

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file and allowed_file(file.filename):
            # Load invalid types from text file
            invalid_types = read_invalid_types(app.config['INVALID_TYPES_FILE'])
            
            # Read the file content
            file_content = file.read()  # Read file content as bytes
            processed_rows, result_or_error = process_csv(file_content, invalid_types)
            
            if processed_rows is None:
                flash(result_or_error, 'error')
                return redirect(request.url)
            
            # Save the processed file to a temporary location
            output_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'sektionsforteckning.csv')
            with open(output_filename, 'w', newline='', encoding='latin-1') as f:
                f.write(result_or_error)
            
            return render_template('index.html', processed_rows=processed_rows, download_link=output_filename)
    
    return render_template('index.html')

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True, download_name='sektionsforteckning.csv')

@app.route('/readme')
def readme():
    # Path to the invalid types file
    invalid_types_file = app.config['INVALID_TYPES_FILE']
    
    # Read the invalid types from the file
    invalid_types = []
    with open(invalid_types_file, 'r', encoding='latin-1') as f:
        invalid_types = [line.strip() for line in f if line.strip()]
    
    return render_template('readme.html', invalid_types=invalid_types)

@app.route('/release_notes')
def release_notes():
    return render_template('release_notes.html')


if __name__ == '__main__':
    app.run(debug=True)
