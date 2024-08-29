import subprocess
import os
from datetime import datetime 
import json


def find_libreoffice():
    try:
        # Try to find LibreOffice installed by Homebrew
        result = subprocess.run(['brew', '--prefix', 'libreoffice'], capture_output=True, text=True)
        libreoffice_path = result.stdout.strip()
        soffice_path = os.path.join(libreoffice_path, 'bin', 'soffice')
        if os.path.exists(soffice_path):
            return soffice_path
    except:
        pass
    
    # If not found, try common locations
    common_paths = [
        '/Applications/LibreOffice.app/Contents/MacOS/soffice',
        '/usr/bin/libreoffice',
        '/usr/bin/soffice',
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None

import subprocess

def convert_to_pdf(input_file):
    libreoffice_path = find_libreoffice()
    if not libreoffice_path:
        raise Exception("LibreOffice not found. Please make sure it's installed.")

    try:
        subprocess.run([
            '/Applications/LibreOffice.app/Contents/MacOS/soffice' ,
            '--headless',
            '--convert-to', 'pdf',
            input_file
        ])
        print(f"PDF generated: {input_file.replace('.docx', '.pdf')}")

        return input_file.replace('.docx', '.pdf')
    
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
