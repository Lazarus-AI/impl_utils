from sync.gdrive.client import download_file, get_info_from_google_url


def download(url_or_id, destination_path):
    # assume file_id and change if it looks like a url
    file_id = url_or_id
    if url_or_id.lower().startswith("http"):
        info = get_info_from_google_url(url_or_id)
        file_id = info.get("file_id")
    return download_file(file_id, destination_path)


def upload(file_path, gdrive_path=None):
    url = ""
    return url
