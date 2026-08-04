import io
import requests
import pandas as pd
import time
import requests

# Your actual SharePoint Site ID
SITE_ID = "2hklct.sharepoint.com,bb483260-ae23-4a2d-bd67-298782ae33e5,608fce08-995c-44e1-a8c4-d2ca3a2881d2"

# -----------------------------
# DOWNLOAD EXCEL FILE
# -----------------------------

def download_file_bytes(file_path, token):
    """
    Downloads a file from SharePoint and returns raw bytes.
    """

    #  Microsoft Graph URL format for your site
    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drive/root:/{file_path}:/content"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to download file: {response.status_code} - {response.text}")

    return response.content

    # Download actual Excel file
    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drive/root:/{file_path}:/content"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    return pd.read_excel(io.BytesIO(resp.content))


# -----------------------------
# UPLOAD FILE TO SHAREPOINT
# -----------------------------
def upload_file_to_sharepoint(sharepoint_path, local_filename, token):
    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drive/root:/{sharepoint_path}:/content"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }

    with open(local_filename, "rb") as f:
        resp = requests.put(url, headers=headers, data=f)
        resp.raise_for_status()

    return True


# -----------------------------
# LIST FILES IN SHAREPOINT FOLDER
# -----------------------------
def list_files_in_sharepoint_folder(folder_path, token):
    """
    Returns full SharePoint paths of all .xlsx files inside a folder.
    """
    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drive/root:/{folder_path}:/children"
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    items = resp.json().get("value", [])
    files = []

    for item in items:
        if item["name"].endswith(".xlsx"):
            files.append(folder_path + item["name"])

    return files


# -----------------------------
# MOVE FILE IN SHAREPOINT
# -----------------------------
def move_file_in_sharepoint(old_path, new_path, token):
    """
    Moves a file by copying it to new_path and deleting the old one.
    """

    # 1. Download file content
    url_download = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drive/root:/{old_path}:/content"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url_download, headers=headers)
    resp.raise_for_status()
    content = resp.content

    # 2. Upload to new location
    url_upload = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drive/root:/{new_path}:/content"
    headers_upload = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    resp_upload = requests.put(url_upload, headers=headers_upload, data=content)
    resp_upload.raise_for_status()

    # 3. Delete old file
    url_delete = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drive/root:/{old_path}"
    resp_delete = requests.delete(url_delete, headers={"Authorization": f"Bearer {token}"})
    resp_delete.raise_for_status()

    return True



def safe_move_file(file_path, new_path, token, retries=5, delay=2):
    for attempt in range(retries):
        try:
            move_file_in_sharepoint(file_path, new_path, token)
            return True
        except requests.exceptions.HTTPError as e:
            if "423" in str(e):
                print(f"File locked, retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                raise e
    print("Failed to move file after retries.")
    return False
