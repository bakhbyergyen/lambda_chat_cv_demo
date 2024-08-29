import subprocess
import os
from datetime import datetime
import json
import platform

def find_libreoffice():
    if platform.system() == "Linux":  # Streamlit uses Linux
        return "/usr/bin/libreoffice"
    elif platform.system() == "Darwin":  # macOS
        result = subprocess.run(['brew', '--prefix', 'libreoffice'], capture_output=True, text=True)
        libreoffice_path = result.stdout.strip()
        soffice_path = os.path.join(libreoffice_path, 'bin', 'soffice')
        if os.path.exists(soffice_path):
            return soffice_path
    else:
        return None

def convert_to_pdf(input_file):
    libreoffice_path = find_libreoffice()
    if not libreoffice_path:
        raise Exception("LibreOffice not found. Please make sure it's installed.")

    try:
        output_file = input_file.replace('.docx', '.pdf')
        subprocess.run([
            libreoffice_path,
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', os.path.dirname(input_file),
            input_file
        ], check=True)
        print(f"PDF generated: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Function to save CV data to a file
def save_cv_data(data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cv_data_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    return filename