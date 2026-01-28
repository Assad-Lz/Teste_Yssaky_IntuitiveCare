"""
Project: ANS Data ETL Pipeline (Technical Assessment)
Author: Yssaky [Seu Sobrenome]
Date: January 2026
Copyright: (c) 2026. All rights reserved.

Description:
    This module handles the extraction of public accounting data from the ANS 
    (Agência Nacional de Saúde Suplementar) FTP server. It targets specific 
    quarterly files for the year 2025, ensuring data availability for downstream 
    processing tasks.

Disclaimer:
    This code is for evaluation purposes only. Commercial use is prohibited.
"""

import os
import requests
import zipfile
import io

# --- Metadata & Configuration ---

# Explicitly defining authorship for runtime use
__author__ = "Yssaky Assad Luz"

# Base URL for the 2025 directory as identified in the FTP inspection
BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/2025/"

# Specific filenames for the available quarters of 2025
# Structure: {Quarter}T{Year}.zip
TARGET_FILES = [
    "1T2025.zip",
    "2T2025.zip",
    "3T2025.zip"
]

def download_and_extract_data():
    """
    Downloads and extracts accounting data files from the ANS public FTP.
    
    Process:
    1. Connects to the ANS FTP server using the BASE_URL.
    2. Iterates through the TARGET_FILES list.
    3. Downloads the ZIP files into memory to minimize I/O overhead.
    4. Extracts the contents directly to the 'data/' local directory.
    
    Raises:
        requests.exceptions.RequestException: If the HTTP request fails.
        zipfile.BadZipFile: If the downloaded content is not a valid zip file.
    """
    # Using the variable defined above
    print(f"[{__author__}] Starting ETL Process - Extraction Phase...")
    
    # Resolve absolute path for data storage to ensure cross-platform compatibility
    current_dir = os.path.dirname(__file__)
    output_dir = os.path.join(current_dir, '..', 'data')

    # Ensure output directory exists before writing
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Directory created: {output_dir}")

    for filename in TARGET_FILES:
        full_url = f"{BASE_URL}{filename}"
        
        print(f"Targeting source: {full_url}")
        
        try:
            # Setting a timeout is good practice to prevent hanging processes
            response = requests.get(full_url, timeout=30)
            
            if response.status_code == 200:
                print(f"Download successful. Extracting payload: {filename}...")
                
                # In-memory extraction avoids writing the temporary .zip to disk
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    z.extractall(output_dir)
                print(f"Artifacts from {filename} successfully stored in /data")
            else:
                print(f"Failed to fetch resource {filename}. HTTP Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Network error while accessing {filename}: {e}")
        except zipfile.BadZipFile:
            print(f"Error: The file {filename} is corrupted or not a valid zip.")
        except Exception as e:
            print(f"Critical error processing {filename}: {str(e)}")

if __name__ == "__main__":
    download_and_extract_data()