from typing import Any, Dict, List, Optional

from lazarus_implementation_tools.sync.microsoft.o365_email import O365EmailClient
from lazarus_implementation_tools.sync.microsoft.onedrive import OneDriveClient
from lazarus_implementation_tools.sync.microsoft.sharepoint import SharePointClient


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


class SharePointUtils:
    def __init__(self, client_id: str, client_secret: str, tenant_id: str, site_name: str):
        """Initialize the SharePointUtils class.

        :param client_id: Client ID for SharePoint authentication
        :param client_secret: Client secret for SharePoint authentication
        :param tenant_id: Tenant ID for SharePoint authentication
        :param site_name: SharePoint site name (from the URL)

        """
        self.client = SharePointClient(client_id, client_secret, tenant_id, site_name)
        self.site_name = site_name

    def authenticate(
        self, auth_code: str, redirect_uri: str, scopes: Optional[List[str]] = None
    ) -> Any:
        """Authenticate with SharePoint using authorization code.

        :param auth_code: Authorization code from OAuth flow
        :param redirect_uri: Redirect URI used in OAuth flow
        :param scopes: List of scopes to request

        :returns: True if authentication successful

        """
        return self.client.authenticate_with_code(auth_code, redirect_uri, scopes)

    def upload_file(self, local_path: str, remote_path: str) -> Any:
        """Upload a file to SharePoint Documents library.

        :param local_path: Local file path
        :param remote_path: Remote path in SharePoint (e.g., "/Documents/myfile.txt")

        :returns: File metadata dict with success status

        """
        return self.client.upload_file(local_path, remote_path)

    def download_file(self, remote_path: str, local_path: Optional[str] = None) -> Any:
        """Download a file from SharePoint.

        :param remote_path: Remote file path or file ID
        :param local_path: Local path to save file (optional)

        :returns: Result dict with success status and file content

        """
        return self.client.download_file_wrapper(remote_path, local_path)

    def move_file(
        self, source_path: str, destination_path: str, new_name: Optional[str] = None
    ) -> Any:
        """Move a file to a new location in SharePoint.

        :param source_path: Source file path or ID
        :param destination_path: Destination folder path or ID
        :param new_name: New file name (optional)

        :returns: Result dict with success status

        """
        return self.client.move_item_wrapper(source_path, destination_path, new_name)

    def delete_file(self, file_path: str) -> Any:
        """Delete a file from SharePoint.

        :param file_path: File path or ID to delete

        :returns: Result dict with success status

        """
        return self.client.delete_item_wrapper(file_path)

    def delete_folder(self, folder_path: str, force: bool = False) -> Any:
        """Delete a folder from SharePoint.

        :param folder_path: Folder path or ID to delete
        :param force: If True, delete even if folder is not empty

        :returns: Result dict with success status

        """
        return self.client.delete_folder(folder_path, force)

    def rename_file(self, file_path: str, new_name: str) -> Any:
        """Rename a file in SharePoint.

        :param file_path: Current file path or ID
        :param new_name: New name for the file

        :returns: Result dict with new file info

        """
        return self.client.rename_file(file_path, new_name)

    def rename_folder(self, folder_path: str, new_name: str) -> Any:
        """Rename a folder in SharePoint.

        :param folder_path: Current folder path or ID
        :param new_name: New name for the folder

        :returns: Result dict with new folder info

        """
        return self.client.rename_folder(folder_path, new_name)

    def create_folder(self, folder_name: str, parent_path: str = "/Documents") -> Any:
        """Create a new folder in SharePoint Documents library.

        :param folder_name: Name of the folder to create
        :param parent_path: Parent folder path (default: /Documents)

        :returns: Folder metadata dict with success status

        """
        return self.client.create_folder_wrapper(folder_name, parent_path)

    def list_files(self, folder_path: str = "/Documents") -> Any:
        """List files and folders in a SharePoint directory.

        :param folder_path: Folder path to list (default: /Documents)

        :returns: Dict with lists of files and folders

        """
        return self.client.list_files(folder_path)

    def search_files(self, query: str, folder_path: Optional[str] = None) -> Any:
        """Search for files and folders in SharePoint.

        :param query: Search query
        :param folder_path: Folder to search in (optional, searches all if None)

        :returns: Search results with success status

        """
        return self.client.search_files(query, folder_path)

    def get_file_info(self, file_path: str) -> Any:
        """Get detailed information about a file or folder.

        :param file_path: File path or ID

        :returns: File information dict with success status

        """
        return self.client.get_file_info(file_path)

    def create_sharing_link(
        self, file_path: str, link_type: str = "view", scope: str = "organization"
    ) -> Any:
        """Create a sharing link for a file.

        :param file_path: File path or ID
        :param link_type: Type of link ('view' or 'edit')
        :param scope: Scope of link ('anonymous' or 'organization')

        :returns: Sharing link information with success status

        """
        return self.client.create_sharing_link(file_path, link_type, scope)


class O365EmailUtils:
    """Office 365 Email utilities wrapper for simplified email operations"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        user_principal_name: str,
        storage_path: str = "stored_emails",
    ):
        """Initialize the O365EmailUtils class

        Args:
            client_id: Client ID for O365 authentication client_secret: Client secret
            for O365 authentication tenant_id: Tenant ID for O365 authentication
            user_principal_name: User's email address storage_path: Path for storing
            emails locally

        """
        self.client = O365EmailClient(client_id, client_secret, tenant_id, user_principal_name)
        self.user_principal_name = user_principal_name
        self.client.init_email_storage(storage_path)

    def authenticate(self, auth_code: str, redirect_uri: str, scopes: Optional[List[str]] = None):
        """Authenticate with Office 365 using authorization code

        Args:
            auth_code: Authorization code from OAuth flow redirect_uri: Redirect URI
            used in OAuth flow scopes: List of scopes to request

        Returns:
            True if authentication successful

        """
        # Call client authentication method
        return self.client.authenticate_with_code(auth_code, redirect_uri, scopes)

    def get_inbox_emails(
        self,
        limit: int = 50,
        unread_only: bool = False,
        include_attachments: bool = True,
        days_back: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get emails from inbox

        Args:
            limit: Maximum number of emails to retrieve unread_only: Only get unread
            emails include_attachments: Include attachment data days_back: Only get
            emails from the last N days

        Returns:
            Dict with success status and messages

        """
        # Call client get_inbox_emails method
        return self.client.get_inbox_emails(limit, unread_only, include_attachments, days_back)

    def send_email(
        self,
        to_recipients: List[str],
        subject: str,
        body: str,
        cc_recipients: Optional[List[str]] = None,
        bcc_recipients: Optional[List[str]] = None,
        attachments: Optional[List[Dict]] = None,
        is_html: bool = False,
    ) -> Dict[str, Any]:
        """Send an email

        Args:
            to_recipients: List of recipient emails subject: Email subject body: Email
            body cc_recipients: CC recipients bcc_recipients: BCC recipients
            attachments: List of attachments (with 'name' and 'content' or 'path')
            is_html: Whether body is HTML

        Returns:
            Result dict with success status

        """
        # Call client send_email method
        return self.client.send_email(
            to_recipients, subject, body, cc_recipients, bcc_recipients, attachments, is_html
        )

    def mark_emails_as_read(self, message_ids: List[str]) -> Dict[str, Any]:
        """Mark multiple emails as read

        Args:
            message_ids: List of message IDs

        Returns:
            Result dict with success/failure counts

        """
        # Call client mark_emails_as_read method
        return self.client.mark_emails_as_read(message_ids)

    def search_emails(
        self, query: str, folder: Optional[str] = None, limit: int = 50
    ) -> Dict[str, Any]:
        """Search for emails

        Args:
            query: Search query folder: Folder to search in (None = all) limit: Maximum
            results

        Returns:
            Search results

        """
        # Call client search_emails method
        return self.client.search_emails(query, folder, limit)

    def store_emails_with_attachments(
        self,
        limit: int = 50,
        unread_only: bool = True,
        days_back: Optional[int] = None,
        mark_as_read: bool = False,
    ) -> Dict[str, Any]:
        """Store emails with attachments to local storage

        Args:
            limit: Number of emails to process unread_only: Only process unread emails
            days_back: Only process emails from last N days mark_as_read: Mark emails as
            read after storing

        Returns:
            Processing results

        """
        # Call client store_emails_with_attachments method
        return self.client.store_emails_with_attachments(
            limit, unread_only, days_back, mark_as_read
        )

    def get_email_statistics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get email statistics

        Args:
            days_back: Number of days to analyze

        Returns:
            Email statistics

        """
        # Call client get_email_statistics method
        return self.client.get_email_statistics(days_back)

    def get_mailbox_info(self) -> Dict[str, Any]:
        """Get mailbox settings and information

        Returns:
            Mailbox information

        """
        # Call client get_mailbox_info method
        return self.client.get_mailbox_info()
