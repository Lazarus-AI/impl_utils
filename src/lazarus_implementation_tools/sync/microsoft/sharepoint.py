import os
import time
from typing import Any, List, Optional
from urllib.parse import quote

import msal
import requests


class SharePointAuthenticationError(Exception):
    """Raised when authentication fails"""

    pass


class SharePointAPIError(Exception):
    """Raised when API requests fail"""

    pass


class SharePointRateLimitError(Exception):
    """Raised when rate limit is hit"""

    pass


class SharePointClient:
    def __init__(self, client_id: str, client_secret: str, tenant_id: str, site_name: str):
        """Initialize SharePoint client

        Args:
            client_id: Azure AD application ID client_secret: Azure AD client secret
            tenant_id: Azure AD tenant ID site_name: SharePoint site name or full URL
            (e.g., "sharepointapitest" or
            "https://lazarusforms.sharepoint.com/sites/sharepointapitest")

        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id

        # Parse site information
        if "sharepoint.com" in site_name:
            # Full URL provided, extract components
            import re

            match = re.match(r"https?://([^/]+)/sites/([^/]+)", site_name)
            if match:
                self.sharepoint_domain = match.group(1)  # e.g., lazarusforms.sharepoint.com
                self.site_name = match.group(2)  # e.g., sharepointapitest
            else:
                # Fallback
                self.sharepoint_domain = site_name.split("/")[2] if "/" in site_name else site_name
                self.site_name = site_name.split("/")[-1]
        else:
            # Just site name provided
            self.site_name = site_name
            # Domain will be determined during authentication
            self.sharepoint_domain = None

        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.authenticated = False
        self.site_id = None
        self.drive_id = None

        # MSAL app for authentication
        self.msal_app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
        )

    def _is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self.authenticated and self.access_token is not None

    def authenticate_with_code(
        self, authorization_code: str, redirect_uri: str, scopes: List[str] = None
    ):
        """Authenticate using authorization code flow"""
        try:
            if scopes is None:
                scopes = [
                    "https://graph.microsoft.com/Sites.ReadWrite.All",
                    "https://graph.microsoft.com/Files.ReadWrite.All",
                    "https://graph.microsoft.com/User.Read",
                ]

            result = self.msal_app.acquire_token_by_authorization_code(
                code=authorization_code, scopes=scopes, redirect_uri=redirect_uri
            )

            if "access_token" in result:
                self.access_token = result["access_token"]
                self.refresh_token = result.get("refresh_token")
                self.token_expires_at = time.time() + result.get("expires_in", 3600)
                self.authenticated = True

                # Get site and drive IDs after authentication
                self._initialize_site_info()

                return True
            else:
                error_msg = result.get("error_description", "Authentication failed")
                raise SharePointAuthenticationError(f"Authentication failed: {error_msg}")

        except Exception as e:
            raise SharePointAuthenticationError(f"Authentication error: {str(e)}")

    def _initialize_site_info(self):
        """Get SharePoint site ID and default document library drive ID"""
        try:
            # Construct the site path based on what we have
            if self.sharepoint_domain:
                # We have the full domain from the URL
                site_path = f"/sites/{self.sharepoint_domain}:/sites/{self.site_name}"
            else:
                # Try to determine the domain
                try:
                    # Get current user info to extract domain
                    user_response = self._make_request("GET", "/me")
                    user_data = user_response.json()

                    # Try to extract domain from user's email
                    mail = user_data.get("mail", "") or user_data.get("userPrincipalName", "")
                    if "@" in mail:
                        # Extract organization name from email domain
                        email_domain = mail.split("@")[1]
                        org_name = email_domain.split(".")[0]
                        self.sharepoint_domain = f"{org_name}.sharepoint.com"
                        site_path = f"/sites/{self.sharepoint_domain}:/sites/{self.site_name}"
                    else:
                        raise Exception("Could not determine SharePoint domain")
                except Exception as e:
                    print(f"Could not determine domain from user info: {e}")
                    # Fallback to tenant-based approach
                    raise Exception("Could not determine SharePoint domain")

            print(f"Attempting to connect to site: {site_path}")

            # Get site ID
            site_response = self._make_request("GET", site_path)
            site_data = site_response.json()
            self.site_id = site_data.get("id")

            print(f"Successfully connected to site ID: {self.site_id}")

            # Get default document library drive ID
            drives_response = self._make_request("GET", f"/sites/{self.site_id}/drives")
            drives = drives_response.json().get("value", [])

            # Find the Documents library
            for drive in drives:
                print(f"Found drive: {drive.get('name')} (type: {drive.get('driveType')})")
                if drive.get("name") == "Documents" or "documentLibrary" in drive.get(
                    "driveType", ""
                ):
                    self.drive_id = drive.get("id")
                    print(f"Using Documents library with drive ID: {self.drive_id}")
                    break

            if not self.drive_id and drives:
                # Fallback to first drive if Documents not found
                self.drive_id = drives[0].get("id")
                print(f"Using first available drive with ID: {self.drive_id}")

            if not self.drive_id:
                print("Warning: No document library found in the site")

        except Exception as e:
            # Log error but don't fail authentication
            print(f"Warning: Could not initialize site info: {str(e)}")
            print("You may need to specify the full SharePoint URL or check site permissions")

    def refresh_access_token(self):
        """Refresh the access token"""
        if not self.refresh_token:
            raise SharePointAuthenticationError("No refresh token available")

        try:
            result = self.msal_app.acquire_token_by_refresh_token(
                refresh_token=self.refresh_token,
                scopes=[
                    "https://graph.microsoft.com/Sites.ReadWrite.All",
                    "https://graph.microsoft.com/Files.ReadWrite.All",
                ],
            )

            if "access_token" in result:
                self.access_token = result["access_token"]
                self.refresh_token = result.get("refresh_token", self.refresh_token)
                self.token_expires_at = time.time() + result.get("expires_in", 3600)
                return True
            else:
                raise SharePointAuthenticationError("Token refresh failed")

        except Exception as e:
            raise SharePointAuthenticationError(f"Token refresh error: {str(e)}")

    def _ensure_valid_token(self):
        """Ensure access token is valid"""
        if not self.access_token:
            raise SharePointAuthenticationError("No access token available")

        if time.time() >= self.token_expires_at - 300:  # Refresh 5 minutes before expiry
            self.refresh_access_token()

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated request to Microsoft Graph API"""
        self._ensure_valid_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers

        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(method, url, **kwargs)

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise SharePointRateLimitError(f"Rate limited. Retry after {retry_after} seconds")

            # Handle other errors
            if not response.ok:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", {}).get(
                    "message", f"HTTP {response.status_code}"
                )
                raise SharePointAPIError(f"API request failed: {error_msg}")

            return response

        except requests.RequestException as e:
            raise SharePointAPIError(f"Request failed: {str(e)}")

    def _get_drive_item_path(self, path: str) -> str:
        """Convert a path to SharePoint drive item format"""
        # Remove /Documents prefix if present
        if path.startswith("/Documents/"):
            path = path[10:]
        elif path.startswith("/Documents"):
            path = path[10:]
        elif path.startswith("/"):
            path = path[1:]

        return path

    def get_item_by_path(self, path: str) -> Any:
        """Get item metadata by path"""
        clean_path = self._get_drive_item_path(path)

        if not clean_path:
            # Root of Documents library
            response = self._make_request("GET", f"/drives/{self.drive_id}/root")
        else:
            encoded_path = quote(clean_path, safe="/")
            response = self._make_request("GET", f"/drives/{self.drive_id}/root:/{encoded_path}")

        return response.json()

    def get_item_by_id(self, item_id: str) -> Any:
        """Get item metadata by ID"""
        response = self._make_request("GET", f"/drives/{self.drive_id}/items/{item_id}")
        return response.json()

    def list_children(self, parent_id: Optional[str] = None, path: Optional[str] = None) -> Any:
        """List children of a folder"""
        if parent_id:
            endpoint = f"/drives/{self.drive_id}/items/{parent_id}/children"
        elif path:
            clean_path = self._get_drive_item_path(path)
            if not clean_path:
                endpoint = f"/drives/{self.drive_id}/root/children"
            else:
                encoded_path = quote(clean_path, safe="/")
                endpoint = f"/drives/{self.drive_id}/root:/{encoded_path}:/children"
        else:
            endpoint = f"/drives/{self.drive_id}/root/children"

        response = self._make_request("GET", endpoint)
        return response.json().get("value", [])

    def list_files(self, folder_path: str = "/Documents") -> Any:
        """List files and folders in a directory"""
        if not self._is_authenticated():
            raise SharePointAuthenticationError("Not authenticated")

        try:
            items = self.list_children(path=folder_path)

            files = []
            folders = []

            for item in items:
                item_info = {
                    "id": item["id"],
                    "name": item["name"],
                    "size": item.get("size", 0),
                    "created": item["createdDateTime"],
                    "modified": item["lastModifiedDateTime"],
                    "web_url": item.get("webUrl"),
                }

                if "folder" in item:
                    folders.append(item_info)
                else:
                    files.append(item_info)

            return {"success": True, "files": files, "folders": folders, "total_items": len(items)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_folder_wrapper(self, folder_name: str, parent_path: str = "/Documents") -> Any:
        """Create a new folder in SharePoint"""
        if not self._is_authenticated():
            raise SharePointAuthenticationError("Not authenticated")

        try:
            folder_data = {
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename",
            }

            clean_path = self._get_drive_item_path(parent_path)

            if not clean_path:
                endpoint = f"/drives/{self.drive_id}/root/children"
            else:
                encoded_path = quote(clean_path, safe="/")
                endpoint = f"/drives/{self.drive_id}/root:/{encoded_path}:/children"

            response = self._make_request("POST", endpoint, json=folder_data)
            result = response.json()

            return {
                "success": True,
                "folder_id": result["id"],
                "name": result["name"],
                "created": result["createdDateTime"],
                "web_url": result.get("webUrl"),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def upload_file(self, local_path: str, destination_path: str) -> Any:
        """Upload a file to SharePoint"""
        if not self._is_authenticated():
            raise SharePointAuthenticationError("Not authenticated")

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")

        # Get file size
        file_size = os.path.getsize(local_path)

        # For files < 4MB, use simple upload
        if file_size < 4 * 1024 * 1024:
            return self._simple_upload(local_path, destination_path, file_size)
        else:
            return self._chunked_upload(local_path, destination_path, file_size)

    def _simple_upload(self, local_path: str, destination_path: str, file_size: int) -> Any:
        """Simple upload for small files (< 4MB)"""
        with open(local_path, "rb") as f:
            content = f.read()

        clean_path = self._get_drive_item_path(destination_path)
        encoded_path = quote(clean_path, safe="/")
        endpoint = f"/drives/{self.drive_id}/root:/{encoded_path}:/content"

        headers = {"Content-Type": "application/octet-stream"}
        result = self._make_request("PUT", endpoint, headers=headers, data=content).json()

        return {
            "success": True,
            "file_id": result.get("id"),
            "name": result.get("name"),
            "size": result.get("size"),
            "created": result.get("createdDateTime"),
            "modified": result.get("lastModifiedDateTime"),
            "web_url": result.get("webUrl"),
            "download_url": result.get("@microsoft.graph.downloadUrl"),
        }

    def _chunked_upload(self, local_path: str, destination_path: str, file_size: int):
        """Chunked upload for large files (>= 4MB)"""
        # Create upload session
        clean_path = self._get_drive_item_path(destination_path)
        encoded_path = quote(clean_path, safe="/")
        endpoint = f"/drives/{self.drive_id}/root:/{encoded_path}:/createUploadSession"

        session_data = {
            "item": {
                "@microsoft.graph.conflictBehavior": "rename",
                "name": os.path.basename(destination_path),
            }
        }

        session_response = self._make_request("POST", endpoint, json=session_data).json()
        upload_url = session_response["uploadUrl"]

        # Upload file in chunks (10MB chunks)
        chunk_size = 10 * 1024 * 1024
        uploaded = 0

        with open(local_path, "rb") as f:
            while uploaded < file_size:
                # Read chunk
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                # Calculate range
                chunk_end = min(uploaded + len(chunk) - 1, file_size - 1)
                content_range = f"bytes {uploaded}-{chunk_end}/{file_size}"

                # Upload chunk
                headers = {"Content-Length": str(len(chunk)), "Content-Range": content_range}

                response = requests.put(upload_url, data=chunk, headers=headers)
                response.raise_for_status()

                uploaded += len(chunk)

                # If this was the last chunk, get the file metadata
                if uploaded >= file_size:
                    result = response.json()
                    return {
                        "success": True,
                        "file_id": result.get("id"),
                        "name": result.get("name"),
                        "size": result.get("size"),
                        "created": result.get("createdDateTime"),
                        "modified": result.get("lastModifiedDateTime"),
                        "web_url": result.get("webUrl"),
                        "download_url": result.get("@microsoft.graph.downloadUrl"),
                    }

        raise SharePointAPIError("Upload completed but no response received")

    def download_file_wrapper(self, remote_path: str, local_path: Optional[str] = None) -> Any:
        """Download a file from SharePoint"""
        if not self._is_authenticated():
            raise SharePointAuthenticationError("Not authenticated")

        try:
            if remote_path.startswith("/"):
                clean_path = self._get_drive_item_path(remote_path)
                encoded_path = quote(clean_path, safe="/")
                endpoint = f"/drives/{self.drive_id}/root:/{encoded_path}:/content"
            else:
                # Assume it's an item ID
                endpoint = f"/drives/{self.drive_id}/items/{remote_path}/content"

            response = self._make_request("GET", endpoint)
            content = response.content

            result = {"success": True, "content": content, "size": len(content)}

            # Save to local file if path provided
            if local_path:
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, "wb") as f:
                    f.write(content)
                result["local_path"] = local_path

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def move_item_wrapper(
        self, source_path: str, destination_path: str, new_name: Optional[str] = None
    ) -> Any:
        """Move an item to a new location"""
        if not self._is_authenticated():
            raise SharePointAuthenticationError("Not authenticated")

        try:
            # Get source item info
            if source_path.startswith("/"):
                source_item = self.get_item_by_path(source_path)
            else:
                source_item = self.get_item_by_id(source_path)

            # Get destination folder info
            if destination_path.startswith("/"):
                dest_item = self.get_item_by_path(destination_path)
            else:
                dest_item = self.get_item_by_id(destination_path)

            # Prepare move data
            move_data = {"parentReference": {"id": dest_item["id"]}}

            if new_name:
                move_data["name"] = new_name  # type: ignore

            # Perform move
            response = self._make_request(
                "PATCH", f"/drives/{self.drive_id}/items/{source_item['id']}", json=move_data
            )
            result = response.json()

            return {
                "success": True,
                "new_id": result["id"],
                "new_name": result["name"],
                "new_path": f"{destination_path}/{result['name']}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_item_wrapper(self, file_path: str) -> Any:
        """Delete a file or folder"""
        if not self._is_authenticated():
            raise SharePointAuthenticationError("Not authenticated")

        try:
            if file_path.startswith("/"):
                clean_path = self._get_drive_item_path(file_path)
                encoded_path = quote(clean_path, safe="/")
                endpoint = f"/drives/{self.drive_id}/root:/{encoded_path}"
            else:
                endpoint = f"/drives/{self.drive_id}/items/{file_path}"

            response = self._make_request("DELETE", endpoint)
            return {"success": response.status_code == 204}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_folder(self, folder_path: str, force: bool = False) -> Any:
        """Delete a folder from SharePoint"""
        if not self._is_authenticated():
            raise SharePointAuthenticationError("Not authenticated")

        try:
            # Check if folder exists and get its info
            if folder_path.startswith("/"):
                folder_item = self.get_item_by_path(folder_path)
            else:
                folder_item = self.get_item_by_id(folder_path)

            # Verify it's actually a folder
            if "folder" not in folder_item:
                return {"success": False, "error": "Item is not a folder"}

            # If not forcing, check if folder is empty
            if not force:
                children = self.list_children(parent_id=folder_item["id"])
                if children:
                    return {
                        "success": False,
                        "error": f"Folder is not empty ({len(children)} items). Use force=True to delete anyway.",
                    }

            # Delete the folder
            return self.delete_item_wrapper(folder_item["id"])

        except Exception as e:
            return {"success": False, "error": str(e)}

    def rename_file(self, file_path: str, new_name: str) -> Any:
        """Rename a file"""
        if not self._is_authenticated():
            raise SharePointAuthenticationError("Not authenticated")

        try:
            # Get file info first
            if file_path.startswith("/"):
                file_item = self.get_item_by_path(file_path)
            else:
                file_item = self.get_item_by_id(file_path)

            # Verify it's a file, not a folder
            if "folder" in file_item:
                return {
                    "success": False,
                    "error": "Item is a folder, not a file. Use rename_folder() instead.",
                }

            # Rename the file
            rename_data = {"name": new_name}
            response = self._make_request(
                "PATCH", f"/drives/{self.drive_id}/items/{file_item['id']}", json=rename_data
            )
            result = response.json()

            # Get parent path
            parent_ref = file_item.get("parentReference", {})
            parent_path = parent_ref.get("path", "").replace("/drive/root:", "/Documents")

            return {
                "success": True,
                "file_id": result["id"],
                "old_name": file_item["name"],
                "new_name": result["name"],
                "new_path": f"{parent_path}/{result['name']}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def rename_folder(self, folder_path: str, new_name: str) -> Any:
        """Rename a folder"""
        if not self._is_authenticated():
            raise SharePointAuthenticationError("Not authenticated")

        try:
            # Get folder info first
            if folder_path.startswith("/"):
                folder_item = self.get_item_by_path(folder_path)
            else:
                folder_item = self.get_item_by_id(folder_path)

            # Verify it's a folder, not a file
            if "folder" not in folder_item:
                return {
                    "success": False,
                    "error": "Item is a file, not a folder. Use rename_file() instead.",
                }

            # Rename the folder
            rename_data = {"name": new_name}
            response = self._make_request(
                "PATCH", f"/drives/{self.drive_id}/items/{folder_item['id']}", json=rename_data
            )
            result = response.json()

            # Get parent path
            parent_ref = folder_item.get("parentReference", {})
            parent_path = parent_ref.get("path", "").replace("/drive/root:", "/Documents")

            return {
                "success": True,
                "folder_id": result["id"],
                "old_name": folder_item["name"],
                "new_name": result["name"],
                "new_path": f"{parent_path}/{result['name']}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_files(self, query: str, folder_path: Optional[str] = None) -> Any:
        """Search for files and folders"""
        if not self._is_authenticated():
            raise SharePointAuthenticationError("Not authenticated")

        try:
            if folder_path:
                # Get folder ID first
                folder_item = self.get_item_by_path(folder_path)
                endpoint = f"/drives/{self.drive_id}/items/{folder_item['id']}/search(q='{query}')"
            else:
                endpoint = f"/drives/{self.drive_id}/root/search(q='{query}')"

            response = self._make_request("GET", endpoint)
            items = response.json().get("value", [])

            results = []
            for item in items:
                parent_ref = item.get("parentReference", {})
                parent_path = parent_ref.get("path", "").replace("/drive/root:", "/Documents")

                results.append(
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "path": f"{parent_path}/{item['name']}",
                        "size": item.get("size", 0),
                        "type": "folder" if "folder" in item else "file",
                        "modified": item["lastModifiedDateTime"],
                    }
                )

            return {"success": True, "results": results, "count": len(results)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_file_info(self, file_path: str) -> Any:
        """Get detailed information about a file or folder"""
        if not self._is_authenticated():
            raise SharePointAuthenticationError("Not authenticated")

        try:
            if file_path.startswith("/"):
                item = self.get_item_by_path(file_path)
            else:
                item = self.get_item_by_id(file_path)

            parent_ref = item.get("parentReference", {})
            parent_path = parent_ref.get("path", "").replace("/drive/root:", "/Documents")

            return {
                "success": True,
                "id": item["id"],
                "name": item["name"],
                "size": item.get("size", 0),
                "type": "folder" if "folder" in item else "file",
                "created": item["createdDateTime"],
                "modified": item["lastModifiedDateTime"],
                "created_by": item.get("createdBy", {}).get("user", {}).get("displayName"),
                "modified_by": item.get("lastModifiedBy", {}).get("user", {}).get("displayName"),
                "path": f"{parent_path}/{item['name']}",
                "download_url": item.get("@microsoft.graph.downloadUrl"),
                "web_url": item.get("webUrl"),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_sharing_link(
        self, file_path: str, link_type: str = "view", scope: str = "anonymous"
    ) -> Any:
        """Create a sharing link for a file"""
        if not self._is_authenticated():
            raise SharePointAuthenticationError("Not authenticated")

        try:
            if file_path.startswith("/"):
                item = self.get_item_by_path(file_path)
                file_id = item["id"]
            else:
                file_id = file_path

            link_data = {
                "type": link_type,  # view, edit
                "scope": scope,  # anonymous, organization
            }

            response = self._make_request(
                "POST", f"/drives/{self.drive_id}/items/{file_id}/createLink", json=link_data
            )
            result = response.json()

            return {
                "success": True,
                "link": result["link"]["webUrl"],
                "type": result["link"]["type"],
                "scope": result["link"]["scope"],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
