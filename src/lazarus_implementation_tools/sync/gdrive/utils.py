from typing import Any, Optional

from .client import GoogleDriveClient


class GoogleDriveUtils:
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        """Initialize the GoogleDriveUtils class.

        :param credentials_path: Path to OAuth2 credentials JSON file
        :param token_path: Path to store access token

        """
        self.client = GoogleDriveClient(credentials_path, token_path)

    def authenticate(self) -> Any:
        """Test authentication by attempting to list files.

        :returns: True if authentication successful

        """
        return self.client.authenticate()

    def upload_file(self, local_path: str, remote_path: str) -> Any:
        """Upload a file to Google Drive.

        :param local_path: Local file path
        :param remote_path: Remote path in Google Drive (folder ID or name)

        :returns: File metadata dict

        """
        return self.client.upload_file(local_path, remote_path)

    def download_file(self, remote_path: str, local_path: Optional[str] = None) -> Any:
        """Download a file from Google Drive.

        :param remote_path: Remote file path or file ID
        :param local_path: Local path to save file (optional)

        :returns: Result dict with success status and file content

        """
        return self.client.download_file_wrapper(remote_path, local_path)

    def delete_file(self, file_path: str) -> Any:
        """Delete a file from Google Drive.

        :param file_path: File path or ID to delete

        :returns: Result dict

        """
        return self.client.delete_item_wrapper(file_path)

    def delete_folder(self, folder_path: str, force: bool = False) -> Any:
        """Delete a folder from Google Drive.

        :param folder_path: Folder path or ID to delete
        :param force: If True, delete even if folder is not empty

        :returns: Result dict

        """
        # Google Drive treats folders like files
        return self.client.delete_item_wrapper(folder_path)

    def create_folder(self, folder_path: str, parent_path: str = "/") -> Any:
        """Create a new folder.

        :param folder_path: Name of the folder to create
        :param parent_path: Parent folder ID (default: root)

        :returns: Folder metadata dict

        """
        return self.client.create_folder_wrapper(folder_path, parent_path)

    def list_files(self, folder_path: str = "/") -> Any:
        """List files and folders in a directory.

        :param folder_path: Folder ID to list (default: root)

        :returns: List of files and folders

        """
        return self.client.list_files(folder_path)

    def search_files(self, query: str, folder_path: Optional[str] = None) -> Any:
        """Search for files and folders.

        :param query: Search query
        :param folder_path: Folder to search in (optional, searches all if None)

        :returns: Search results

        """
        return self.client.search_files(query, folder_path)

    def get_file_info(self, file_path: str) -> Any:
        """Get detailed information about a file or folder.

        :param file_path: File path or ID

        :returns: File information dict

        """
        return self.client.get_file_info(file_path)

    def create_sharing_link(
        self, file_path: str, link_type: str = "view", scope: str = "anonymous"
    ) -> Any:
        """Create a sharing link for a file.

        :param file_path: File path or ID
        :param link_type: Type of link ('view' or 'edit')
        :param scope: Scope of link ('anonymous' or 'organization')

        :returns: Sharing link information

        """
        return self.client.create_sharing_link(file_path, link_type, scope)
