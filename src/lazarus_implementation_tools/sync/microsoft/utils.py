from typing import Any, List, Optional

from lazarus_implementation_tools.sync.microsoft.onedrive import OneDriveClient


class OneDriveUtils:
    def __init__(self, client_id: str, client_secret: str, tenant_id: str = "common"):
        """Initialize the OneDriveUtils class.

        :param client_id: Client ID for OneDrive authentication
        :param client_secret: Client secret for OneDrive authentication
        :param tenant_id: Tenant ID for OneDrive authentication (default: common)

        """
        self.client = OneDriveClient(client_id, client_secret, tenant_id)

    def authenticate(
        self, auth_code: str, redirect_uri: str, scopes: Optional[List[str]] = None
    ) -> Any:
        """Authenticate with OneDrive using authorization code.

        :param auth_code: Authorization code from OAuth flow
        :param redirect_uri: Redirect URI used in OAuth flow
        :param scopes: List of scopes to request (defaults to Files.ReadWrite)

        :returns: True if authentication successful

        """
        return self.client.authenticate_with_code(auth_code, redirect_uri, scopes)

    def upload_file(self, local_path: str, remote_path: str) -> Any:
        """Upload a file to OneDrive.

        :param local_path: Local file path
        :param remote_path: Remote path in OneDrive (e.g., "/Documents/myfile.txt")

        :returns: File metadata dict

        """
        return self.client.upload_file(local_path, remote_path)

    def download_file(self, remote_path: str, local_path: Optional[str] = None) -> Any:
        """Download a file from OneDrive.

        :param remote_path: Remote file path or file ID
        :param local_path: Local path to save file (optional)

        :returns: Result dict with success status and file content

        """
        return self.client.download_file_wrapper(remote_path, local_path)

    def move_file(
        self, source_path: str, destination_path: str, new_name: Optional[str] = None
    ) -> Any:
        """Move a file to a new location.

        :param source_path: Source file path or ID
        :param destination_path: Destination folder path or ID
        :param new_name: New file name (optional)

        :returns: Result dict

        """
        return self.client.move_item_wrapper(source_path, destination_path, new_name)

    def delete_file(self, file_path: str) -> Any:
        """Delete a file from OneDrive.

        :param file_path: File path or ID to delete

        :returns: Result dict

        """
        return self.client.delete_item_wrapper(file_path)

    def delete_folder(self, folder_path: str, force: bool = False) -> Any:
        """Delete a folder from OneDrive.

        :param folder_path: Folder path or ID to delete
        :param force: If True, delete even if folder is not empty

        :returns: Result dict

        """
        return self.client.delete_folder(folder_path, force)

    def rename_file(self, file_path: str, new_name: str) -> Any:
        """Rename a file.

        :param file_path: Current file path or ID
        :param new_name: New name for the file

        :returns: Result dict with new file info

        """
        return self.client.rename_file(file_path, new_name)

    def rename_folder(self, folder_path: str, new_name: str) -> Any:
        """Rename a folder.

        :param folder_path: Current folder path or ID
        :param new_name: New name for the folder

        :returns: Result dict with new folder info

        """
        return self.client.rename_folder(folder_path, new_name)

    def update_file_metadata(self, file_path: str, description: Optional[str] = None) -> Any:
        """Update file metadata (description and custom properties).

        :param file_path: File path or ID
        :param description: New description for the file

        :returns: Result dict with updated metadata

        """
        return self.client.update_file_metadata(file_path, description)

    def update_folder_metadata(self, folder_path: str, description: Optional[str] = None) -> Any:
        """Update folder metadata (description).

        :param folder_path: Folder path or ID
        :param description: New description for the folder

        :returns: Result dict with updated metadata

        """
        return self.client.update_folder_metadata(folder_path, description)

    def create_folder(self, folder_path: str, parent_path: str = "/") -> Any:
        """Create a new folder.

        :param folder_path: Name of the folder to create
        :param parent_path: Parent folder path (default: root)

        :returns: Folder metadata dict

        """
        return self.client.create_folder_wrapper(folder_path, parent_path)

    def list_files(self, folder_path: str = "/") -> Any:
        """List files and folders in a directory.

        :param folder_path: Folder path to list (default: root)

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
