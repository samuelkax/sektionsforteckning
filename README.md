# Sektionsförteckning Flask Application

## Overview

This Flask application processes CSV files to generate a section listing. It checks the third row of the uploaded CSV file for a specific value ("Rapport konfiguration") and then processes the data starting from the 13th row. The processed data is displayed in a table and can be downloaded as a new CSV file.

## Features

- **Upload CSV File**: Users can upload a CSV file to be processed.
- **Validation Check**: The application checks if the third row of the uploaded file contains the expected string.
- **Data Processing**: Begins processing from the 13th row and filters out unwanted data based on device types.
- **Download Processed Data**: Users can download the processed data as a CSV file.

## Prerequisites

- Python 3.x
- Flask
- Any text editor or IDE for running and editing the application

## Setup and Installation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/yourusername/sektionsforteckning-flask-app.git
    cd sektionsforteckning-flask-app
    ```

2. **Create a virtual environment**:

    ```bash
    python -m venv venv
    ```

3. **Activate the virtual environment**:

    - **Windows**:

        ```bash
        venv\Scripts\activate
        ```

    - **macOS/Linux**:

        ```bash
        source venv/bin/activate
        ```

4. **Install the required packages**:

    ```bash
    pip install -r requirements.txt
    ```

5. **Run the application**:

    ```bash
    python app.py
    ```

6. **Access the application**:

    Open a web browser and go to `http://127.0.0.1:5000` to access the application.

## Usage

1. **Upload a CSV File**: Click the "Upload" button and select a CSV file to process.
2. **Check for Errors**: If the file does not meet the expected criteria (e.g., the third row does not contain "Rapport konfiguration"), an error message will be displayed.
3. **View Processed Data**: If the file is processed successfully, the processed data will be displayed in a table.
4. **Download Processed CSV**: Click the "Download Processed CSV" button to download the processed data.

## File Structure

- `app.py`: The main Flask application file.
- `templates/`: Directory containing HTML templates.
    - `index.html`: Main HTML template for uploading and displaying data.
- `processed_files/`: Directory where processed CSV files are stored.
- `invalid_types.txt`: Text file containing device types to be filtered out during processing.

## Customization

- **Change Allowed File Types**: Modify `app.config['ALLOWED_EXTENSIONS']` in `app.py` to change the allowed file types for upload.
- **Change Invalid Device Types**: Edit `invalid_types.txt` to update the list of device types that should be excluded during processing.

## Contributing

If you would like to contribute to this project, please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

