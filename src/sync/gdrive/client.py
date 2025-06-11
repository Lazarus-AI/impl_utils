import io
import logging
import os
from typing import Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

FILE = "file"
FOLDER = "folder"
UNKNOWN = "unknown"

# Scopes required for Google Drive API
SCOPES = ["https://www.googleapis.com/auth/drive"]

logger = logging.getLogger(__name__)


class GoogleDriveAuthenticationError(Exception):
    """Raised when authentication fails"""

    pass


class GoogleDriveAPIError(Exception):
    """Raised when API requests fail"""

    pass


class GoogleDriveRateLimitError(Exception):
    """Raised when rate limit is hit"""

    pass


class GoogleDriveClient:
    """Google Drive API client for CRUD operations."""

    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        """Initialize the Google Drive client.

        Args:
            credentials_path: Path to the OAuth2 credentials JSON file token_path: Path
            to store the access token

        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.authenticated = False

    def _is_authenticated(self) -> Any:
        """Check if client is authenticated"""
        return self.authenticated and self.service is not None

    def authenticate(self) -> Any:
        """Authenticate with Google Drive API."""
        creds = None

        try:
            # Load existing token
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except FileNotFoundError:
                logger.info("Token file not found")

            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        logger.error(f"Error refreshing credentials: {e}")
                        creds = None

                if not creds:
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_path, SCOPES
                        )
                        creds = flow.run_local_server(port=0)
                    except FileNotFoundError:
                        logger.error(f"Credentials file not found: {self.credentials_path}")
                        raise GoogleDriveAuthenticationError(
                            f"Credentials file not found: {self.credentials_path}"
                        )

                # Save the credentials for the next run
                try:
                    with open(self.token_path, "w") as token:
                        token.write(creds.to_json())
                except Exception as e:
                    logger.error(f"Error saving token: {e}")

            try:
                self.service = build("drive", "v3", credentials=creds)
                self.authenticated = True
                logger.info("Successfully authenticated with Google Drive API")
            except Exception as e:
                logger.error(f"Error building service: {e}")
                raise GoogleDriveAuthenticationError(f"Error building service: {e}")
            return True
        except Exception as e:
            print(f"Authentication exception: {e}")
            return False

    def _ensure_valid_authentication(self) -> Any:
        """Ensure we have valid authentication"""
        if not self._is_authenticated():
            raise GoogleDriveAuthenticationError("Not authenticated")

    def get_info_from_google_url(self, url: str) -> Any:
        """Parse a Google Drive URL and return information about the resource.

        Args:
            url: The URL of the Google Drive resource

        Returns:
            Dictionary containing type, sub_type, and file_id

        """
        file_indicators = ["presentation", "document", "spreadsheets"]
        folder_indicators = ["folders"]

        fluff = ["http:", "https:", "d", "drive", "docs.google.com", "drive.google.com", ""]
        url_parts = url.split("/")
        details = [part.lower() for part in url_parts if part not in fluff]

        if len(details) < 2:
            raise ValueError("Invalid Google Drive URL format")

        type_indicator = details[0]
        file_id = details[1]
        resource_type = FILE
        sub_type = UNKNOWN

        if type_indicator in folder_indicators:
            resource_type = FOLDER
            sub_type = FOLDER
        elif type_indicator in file_indicators:
            resource_type = FILE
            sub_type = type_indicator

        return {
            "type": resource_type,
            "sub_type": sub_type,
            "file_id": file_id,
        }

    def download_file_wrapper(self, remote_path: str, local_path: Optional[str] = None) -> Any:
        """Download a file from Google Drive.

        Args:
            remote_path: File ID or URL local_path: Local path to save file (optional)

        Returns:
            Result dict with success status and content

        """
        if not self._is_authenticated():
            raise GoogleDriveAuthenticationError("Not authenticated")

        try:
            # Extract file ID if URL provided
            file_id = remote_path
            if remote_path.lower().startswith("http"):
                info = self.get_info_from_google_url(remote_path)
                file_id = info.get("file_id")

            # Download file
            request = self.service.files().get_media(fileId=file_id)  # type: ignore
            file_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(file_buffer, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                logger.debug(f"Download {int(status.progress() * 100)}% of {file_id}")

            content = file_buffer.getvalue()
            result = {"success": True, "content": content, "size": len(content)}

            # Save to local file if path provided
            if local_path:
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, "wb") as f:
                    f.write(content)
                result["local_path"] = local_path

            logger.info(f"Successfully downloaded file {file_id}")
            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def upload_file(
        self, local_path: str, destination_path: str = None, new_name: str = None
    ) -> Any:
        """Upload a file to Google Drive.

        Args:
            local_path: Path to the local file destination_path: Destination folder ID,
            folder name, or Google Drive URL (optional - uploads to root if None)
            new_name: Custom name for the uploaded file (optional - uses original
            filename if None)

        Returns:
            Dict containing file metadata including id, name, size, etc.

        """
        if not self._is_authenticated():
            raise GoogleDriveAuthenticationError("Not authenticated")

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")

        try:
            file_name = new_name or os.path.basename(local_path)
            mimetype = self._get_mimetype_by_extension(file_name)

            file_metadata = {"name": file_name}

            # Handle destination folder
            if destination_path:
                folder_id = self._resolve_folder_id(destination_path)
                if folder_id:
                    file_metadata["parents"] = [folder_id]  # type: ignore
                else:
                    logger.warning(
                        f"Could not resolve folder: {destination_path}. Uploading to root."
                    )

            media = MediaFileUpload(local_path, mimetype=mimetype)

            result = (
                self.service.files()  # type: ignore
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, name, size, createdTime, modifiedTime, webViewLink, parents",
                )
                .execute()
            )

            return {
                "success": True,
                "file_id": result.get("id"),
                "name": result.get("name"),
                "size": result.get("size"),
                "created": result.get("createdTime"),
                "modified": result.get("modifiedTime"),
                "web_url": result.get("webViewLink"),
                "parents": result.get("parents", []),
            }

        except Exception as e:
            logger.error(f"Error uploading file {local_path}: {e}")
            return {"success": False, "error": str(e)}

    def _resolve_folder_id(self, folder_identifier: str) -> Any:
        """Resolve a folder identifier (ID, name, or URL) to a folder ID.

        Args:
            folder_identifier: Folder ID, folder name, or Google Drive URL

        Returns:
            Folder ID if found, None otherwise

        """
        if not folder_identifier:
            return None

        # If it's already a folder ID (looks like a Google Drive ID)
        if len(folder_identifier) > 20 and not folder_identifier.startswith("http"):
            # Verify it's actually a folder
            try:
                file_info = (
                    self.service.files()  # type: ignore
                    .get(fileId=folder_identifier, fields="id, name, mimeType")
                    .execute()
                )

                if file_info.get("mimeType") == "application/vnd.google-apps.folder":
                    return folder_identifier
            except Exception:
                pass

        # If it's a Google Drive URL
        if folder_identifier.startswith("http"):
            try:
                if "/folders/" in folder_identifier:
                    folder_id = folder_identifier.split("/folders/")[1].split("/")[0]
                    # Verify it exists
                    file_info = (
                        self.service.files()  # type: ignore
                        .get(fileId=folder_id, fields="id, name, mimeType")
                        .execute()
                    )

                    if file_info.get("mimeType") == "application/vnd.google-apps.folder":
                        return folder_id
            except Exception:
                pass

        # If it's a folder name, search for it
        try:
            query = f"name='{folder_identifier}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()  # type: ignore

            files = results.get("files", [])
            if files:
                # Return the first match
                return files[0]["id"]

        except Exception as e:
            logger.error(f"Error searching for folder {folder_identifier}: {e}")

        return None

    def delete_item_wrapper(self, file_path: str) -> Any:
        """Delete a file from Google Drive.

        Args:
            file_path: File ID or URL to delete

        Returns:
            Result dict

        """
        if not self._is_authenticated():
            raise GoogleDriveAuthenticationError("Not authenticated")

        try:
            # Extract file ID if URL provided
            file_id = file_path
            if file_path.lower().startswith("http"):
                info = self.get_info_from_google_url(file_path)
                file_id = info.get("file_id")

            self.service.files().delete(fileId=file_id).execute()  # type: ignore
            logger.info(f"Successfully deleted file {file_id}")
            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_files(self, folder_path: str = "/") -> Any:
        """List files in Google Drive.

        Args:
            folder_path: Folder ID to list (default: root)

        Returns:
            List of files and folders

        """
        if not self._is_authenticated():
            raise GoogleDriveAuthenticationError("Not authenticated")

        try:
            # Build query
            search_query = "trashed=false"
            if folder_path != "/" and folder_path:
                search_query += f" and '{folder_path}' in parents"

            results = (
                self.service.files()  # type: ignore
                .list(
                    q=search_query,
                    pageSize=100,
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, parents)",
                )
                .execute()
            )

            items = results.get("files", [])
            files = []
            folders = []

            for item in items:
                item_info = {
                    "id": item["id"],
                    "name": item["name"],
                    "size": item.get("size", 0),
                    "created": item.get("createdTime", ""),
                    "modified": item["modifiedTime"],
                }

                if item["mimeType"] == "application/vnd.google-apps.folder":
                    folders.append(item_info)
                else:
                    files.append(item_info)

            return {"success": True, "files": files, "folders": folders, "total_items": len(items)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_folder_wrapper(self, folder_path: str, parent_path: str = "/") -> Any:
        """Create a folder in Google Drive.

        Args:
            folder_path: Name of the folder to create parent_path: Parent folder ID
            (default: root)

        Returns:
            Folder metadata dict

        """
        if not self._is_authenticated():
            raise GoogleDriveAuthenticationError("Not authenticated")

        try:
            file_metadata = {"name": folder_path, "mimeType": "application/vnd.google-apps.folder"}

            if parent_path != "/":
                file_metadata["parents"] = [parent_path]  # type: ignore

            result = (
                self.service.files()  # type: ignore
                .create(body=file_metadata, fields="id, name, createdTime")
                .execute()
            )

            return {
                "success": True,
                "folder_id": result.get("id"),
                "name": result.get("name"),
                "created": result.get("createdTime"),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_files(self, query: str, folder_path: Optional[str] = None) -> Any:
        """Search for files and folders.

        Args:
            query: Search query folder_path: Folder ID to search in (optional)

        Returns:
            Search results

        """
        if not self._is_authenticated():
            raise GoogleDriveAuthenticationError("Not authenticated")

        try:
            search_query = f"name contains '{query}' and trashed=false"
            if folder_path:
                search_query += f" and '{folder_path}' in parents"

            results = (
                self.service.files()  # type: ignore
                .list(
                    q=search_query,
                    pageSize=50,
                    fields="files(id, name, mimeType, size, modifiedTime, parents, webViewLink)",
                )
                .execute()
            )

            items = results.get("files", [])
            search_results = []

            for item in items:
                search_results.append(
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "path": f"/{item['name']}",  # Simplified path
                        "size": item.get("size", 0),
                        "type": "folder"
                        if item["mimeType"] == "application/vnd.google-apps.folder"
                        else "file",
                        "modified": item["modifiedTime"],
                    }
                )

            return {"success": True, "results": search_results, "count": len(search_results)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_file_info(self, file_path: str) -> Any:
        """Get detailed information about a file or folder.

        Args:
            file_path: File ID or URL

        Returns:
            File information dict

        """
        if not self._is_authenticated():
            raise GoogleDriveAuthenticationError("Not authenticated")

        try:
            # Extract file ID if URL provided
            file_id = file_path
            if file_path.lower().startswith("http"):
                info = self.get_info_from_google_url(file_path)
                file_id = info.get("file_id")

            result = (
                self.service.files()  # type: ignore
                .get(
                    fileId=file_id,
                    fields="id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink",
                )
                .execute()
            )

            return {
                "success": True,
                "id": result["id"],
                "name": result["name"],
                "size": result.get("size", 0),
                "type": "folder"
                if result["mimeType"] == "application/vnd.google-apps.folder"
                else "file",
                "created": result.get("createdTime"),
                "modified": result["modifiedTime"],
                "path": f"/{result['name']}",  # Simplified path
                "web_url": result.get("webViewLink"),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_sharing_link(
        self, file_path: str, link_type: str = "view", scope: str = "anonymous"
    ) -> Any:
        """Create a sharing link for a file.

        Args:
            file_path: File ID or URL link_type: Type of link ('view' or 'edit') - not
            directly applicable to Google Drive scope: Scope of link ('anonymous' or
            'organization')

        Returns:
            Sharing link information

        """
        if not self._is_authenticated():
            raise GoogleDriveAuthenticationError("Not authenticated")

        try:
            # Extract file ID if URL provided
            file_id = file_path
            if file_path.lower().startswith("http"):
                info = self.get_info_from_google_url(file_path)
                file_id = info.get("file_id")

            # Create permission for sharing
            permission = {
                "type": "anyone" if scope == "anonymous" else "domain",
                "role": "reader" if link_type == "view" else "writer",
            }

            self.service.permissions().create(fileId=file_id, body=permission).execute()  # type: ignore

            # Get the web view link
            file_info = self.service.files().get(fileId=file_id, fields="webViewLink").execute()  # type: ignore

            return {
                "success": True,
                "link": file_info.get("webViewLink"),
                "type": link_type,
                "scope": scope,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_mimetype_by_extension(self, filename: str) -> Any:
        """Get MIME type based on file extension.

        Args:
            filename: Name of the file

        Returns:
            MIME type string

        """
        file_extension_mimetypes = {
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pdf": "application/pdf",
            ".csv": "text/csv",
            ".json": "application/json",
            ".txt": "text/plain",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".zip": "application/zip",
        }

        _, extension = os.path.splitext(filename)
        return file_extension_mimetypes.get(extension.lower(), "application/octet-stream")
