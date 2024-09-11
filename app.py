from flask import Flask, render_template, request, send_file, redirect, url_for, Response, flash
import pandas as pd
import os

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

# Read lookup data from device_types.txt
# Den här funktionen läser filen som innehåller enheter till artikelnummer och objektskod
def load_lookup():
    lookup_artnr = {}
    lookup_object_code = {}
    try:
        with open('device_types.txt', 'r') as file:
            for line in file:
                # Split the line into three parts: device_type, article_number, object_code
                device_type, article_number, object_code = line.strip().split(';')
                lookup_artnr[device_type] = article_number
                lookup_object_code[device_type] = object_code
    except FileNotFoundError:
        print("Error: 'device_types.txt' not found.")
    except ValueError:
        print("Error: Incorrect formatting in 'device_types.txt'.")
    
    return lookup_artnr, lookup_object_code

# Function to read invalid types from the file
# Den här funktionen läser filen som innehåller enheter som inte ska vara med i sektionsförteckningen
def read_invalid_types(file_path):
    invalid_types = set()
    try:
        with open(file_path, 'r', encoding='latin-1') as f:
            for line in f:
                invalid_types.add(line.strip())
    except FileNotFoundError:
        print(f"Error: '{file_path}' not found.")
    return invalid_types

# Function to process the CSV and make modifications
def process_csv_mbiz(file_path, lookup_data_artnr, lookup_data_object_code):

    # Skip the first few irrelevant rows (assuming actual data starts from row 12)
    csv_data = pd.read_csv(file_path, sep=';', skiprows=11, encoding='ISO-8859-1', dtype={'Address': str})

    # Rename the columns to match your input structure
    csv_data.columns = ['Panel', 'Zone', 'Address', 'Device type', 'Input function', 'Protocol', 'Customer text']

    # Create a DataFrame for mbizSheet (the output CSV)
    mbiz_data = pd.DataFrame()

    # Fill 'Antal' with the number '1'
    mbiz_data['Antal'] = [1] * len(csv_data)
    
    # Modify 'UNR/Adress' column by concatenating with '=H1' and add object code and address
    mbiz_data['UNR/Adress'] = "=H1" + csv_data['Device type'].apply(lambda x: lookup_data_object_code.get(x, 'Not Found')) + csv_data['Address']

    # Copy 'Sektionsnummer' from 'Zone'
    mbiz_data['Sektionsnummer'] = csv_data['Zone']

    # Copy 'Placering rum' from 'Customer text'
    mbiz_data['Placering rum'] = csv_data['Customer text']

    # Lookup the value in 'Device type' from 'device_types.txt' and fill 'Artikelnummer'
    mbiz_data['Artikelnummer'] = csv_data['Device type'].apply(lambda x: lookup_data_artnr.get(x, 'Not Found'))

    # Save the modified DataFrame to a new CSV
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'import_till_mbiz.csv')
    mbiz_data.to_csv(output_path, index=False, sep=';')
    
    return output_path

# Function to process CSV data and return as a list of rows
def process_csv(file_path, invalid_types):
    # Read the CSV content into a pandas DataFrame, skipping the first 12 rows
    csv_data = pd.read_csv(file_path, sep=';', skiprows=11, encoding='ISO-8859-1', dtype={'Address': str})
    
    # Rename the columns to match your input structure
    csv_data.columns = ['Panel', 'Zone', 'Address', 'Device type', 'Input function', 'Protocol', 'Customer text']
    
    # Filter out invalid device types
    csv_data = csv_data[~csv_data['Device type'].isin(invalid_types)]
    
    # Group by the 'Zone' and aggregate the addresses
    sektionsforteckning = csv_data.groupby('Zone')['Address'].apply(list).reset_index()
    
    # Apply the shorten_address_list function to each group
    sektionsforteckning['Address'] = sektionsforteckning['Address'].apply(lambda x: ", ".join(shorten_address_list(x)))

    # Save the processed sektionsforteckning DataFrame to a new CSV
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'sektionsforteckning.csv')
    sektionsforteckning.to_csv(output_path, index=False, sep=';')
    
    # Return the path to the saved CSV file
    return output_path


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
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file and allowed_file(file.filename):
            # Save the file to a temporary location
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)  # Save the uploaded file to a specific path

            # Step 1: Check if the third row contains "Rapport konfiguration"
            try:
                # Read only the first 3 rows to check the third row content
                first_rows = pd.read_csv(file_path, sep=';', nrows=3, header=None, skiprows=1, encoding='ISO-8859-1')

                # Extract only the first column (where "Rapport konfiguration" should be)
                second_row = first_rows.iloc[1, 0]  # Get the first column value from the third row

                # Check if "Rapport konfiguration" is in the third row's first column
                if "Rapport konfiguration" not in str(second_row):
                    flash('Invalid file format: Det verkar inte vara en korrekt Schneider-fil. Den andra raden måste innehålla "Rapport konfiguration".', 'error')
                    return redirect(request.url)
            except Exception as e:
                flash(f"Error reading the file: {str(e)}", 'error')
                return redirect(request.url)

            # Proceed with loading lookup data and processing the CSV files if the check passes
            lookup_data_artnr, lookup_data_H1_type = load_lookup()  # Load device type data
            invalid_types = read_invalid_types(app.config['INVALID_TYPES_FILE'])  # Load invalid types

            # Process first CSV (mbiz) with the saved file path and lookup data
            output_import_to_mbiz_path = process_csv_mbiz(file_path, lookup_data_artnr, lookup_data_H1_type)

            # Process second CSV (sektionsforteckning) with invalid types
            output_sektionsforteckning_path = process_csv(file_path, invalid_types)

            # Load the processed sektionsforteckning data to pass to the template
            df_sektionsforteckning = pd.read_csv(output_sektionsforteckning_path, sep=';')
            processed_rows = df_sektionsforteckning.values.tolist()

            # Return the page with download links for both CSVs and the table data
            return render_template('index.html', 
                                   download_links=[output_import_to_mbiz_path, output_sektionsforteckning_path], 
                                   processed_rows=processed_rows)

    return render_template('index.html')




@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True, download_name=os.path.basename(filename))

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
