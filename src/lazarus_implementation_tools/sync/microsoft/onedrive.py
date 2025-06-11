import os
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import msal
import requests


class OneDriveAuthenticationError(Exception):
    """Raised when authentication fails"""

    pass


class OneDriveAPIError(Exception):
    """Raised when API requests fail"""

    pass


class OneDriveRateLimitError(Exception):
    """Raised when rate limit is hit"""

    pass


class OneDriveClient:
    def __init__(self, client_id: str, client_secret: str, tenant_id: str = "common"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.authenticated = False

        # MSAL app for authentication
        self.msal_app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
        )

    def _is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self.authenticated and self.access_token is not None

    def authenticate_with_code(self, authorization_code: str, redirect_uri: str, scopes: List[str]):
        try:
            if scopes is None:
                scopes = ["https://graph.microsoft.com/Files.ReadWrite"]

            result = self.msal_app.acquire_token_by_authorization_code(
                code=authorization_code, scopes=scopes, redirect_uri=redirect_uri
            )

            if "access_token" in result:
                self.access_token = result["access_token"]
                self.refresh_token = result.get("refresh_token")
                self.token_expires_at = time.time() + result.get("expires_in", 3600)
                self.authenticated = True
                return True
            else:
                error_msg = result.get("error_description", "Authentication failed")
                raise OneDriveAuthenticationError(f"Authentication failed: {error_msg}")

        except Exception as e:
            raise OneDriveAuthenticationError(f"Authentication error: {str(e)}")

    def refresh_access_token(self):
        if not self.refresh_token:
            raise OneDriveAuthenticationError("No refresh token available")

        try:
            result = self.msal_app.acquire_token_by_refresh_token(
                refresh_token=self.refresh_token,
                scopes=["https://graph.microsoft.com/Files.ReadWrite"],
            )

            if "access_token" in result:
                self.access_token = result["access_token"]
                self.refresh_token = result.get("refresh_token", self.refresh_token)
                self.token_expires_at = time.time() + result.get("expires_in", 3600)
                return True
            else:
                raise OneDriveAuthenticationError("Token refresh failed")

        except Exception as e:
            raise OneDriveAuthenticationError(f"Token refresh error: {str(e)}")

    def _ensure_valid_token(self):
        if not self.access_token:
            raise OneDriveAuthenticationError("No access token available")

        if time.time() >= self.token_expires_at - 300:  # Refresh 5 minutes before expiry
            self.refresh_access_token()

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
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
                raise OneDriveRateLimitError(f"Rate limited. Retry after {retry_after} seconds")

            # Handle other errors
            if not response.ok:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", {}).get(
                    "message", f"HTTP {response.status_code}"
                )
                raise OneDriveAPIError(f"API request failed: {error_msg}")

            return response

        except requests.RequestException as e:
            raise OneDriveAPIError(f"Request failed: {str(e)}")

    def get_item_by_id(self, item_id: str) -> Any:
        response = self._make_request("GET", f"/me/drive/items/{item_id}")
        return response.json()

    def get_item_by_path(self, path: str) -> Any:
        encoded_path = quote(path, safe="/")
        response = self._make_request("GET", f"/me/drive/root:/{encoded_path}")
        return response.json()

    def list_children(self, parent_id: Optional[str] = None, path: Optional[str] = None) -> Any:
        if parent_id:
            endpoint = f"/me/drive/items/{parent_id}/children"
        elif path:
            encoded_path = quote(path, safe="/")
            endpoint = f"/me/drive/root:/{encoded_path}:/children"
        else:
            endpoint = "/me/drive/root/children"

        response = self._make_request("GET", endpoint)
        return response.json().get("value", [])

    def list_files(self, folder_path: str = "/") -> Any:
        if not self._is_authenticated():
            raise OneDriveAuthenticationError("Not authenticated")
        try:
            if folder_path == "/":
                items = self.list_children()
            else:
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
                }

                if "folder" in item:
                    folders.append(item_info)
                else:
                    files.append(item_info)

            return {"success": True, "files": files, "folders": folders, "total_items": len(items)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_folder_wrapper(self, folder_path: str, parent_path: str = "/") -> Any:
        if not self._is_authenticated():
            raise OneDriveAuthenticationError("Not authenticated")

        def create_folder(
            name: str, parent_id: Optional[str] = None, parent_path: Optional[str] = None
        ) -> Any:
            folder_data = {
                "name": name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename",
            }

            if parent_id:
                endpoint = f"/me/drive/items/{parent_id}/children"
            elif parent_path:
                encoded_path = quote(parent_path, safe="/")
                endpoint = f"/me/drive/root:/{encoded_path}:/children"
            else:
                endpoint = "/me/drive/root/children"

            response = self._make_request("POST", endpoint, json=folder_data)
            return response.json()

        try:
            if parent_path == "/":
                result = create_folder(folder_path)
            else:
                result = create_folder(folder_path, parent_path=parent_path)

            return {
                "success": True,
                "folder_id": result["id"],
                "name": result["name"],
                "created": result["createdDateTime"],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def upload_file(self, local_path: str, destination_path: str) -> Any:
        """Upload a file to OneDrive (automatically handles small and large files)

        Args:
            local_path: Path to the local file destination_path: Destination path in
            OneDrive (e.g., /Documents/file.pdf)

        Returns:
            Dict containing file metadata including id, name, size, etc.

        """
        if not self._is_authenticated():
            raise OneDriveAuthenticationError("Not authenticated")

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")

        # Get file size
        file_size = os.path.getsize(local_path)
        file_name = os.path.basename(local_path)

        # For files < 4MB, use simple upload
        if file_size < 4 * 1024 * 1024:
            return self._simple_upload(local_path, destination_path, file_size)
        else:
            return self._chunked_upload(local_path, destination_path, file_size)

    def _simple_upload(self, local_path: str, destination_path: str, file_size: int) -> Any:
        """Internal method for simple upload (< 4MB)"""
        with open(local_path, "rb") as f:
            content = f.read()

        encoded_path = quote(destination_path, safe="/")
        endpoint = f"/me/drive/root:/{encoded_path}:/content"

        headers = {"Content-Type": "application/octet-stream"}
        result = self._make_request("PUT", endpoint, headers=headers, data=content).json()

        return {
            "success": True,
            "file_id": result.get("id"),
            "name": result.get("name"),
            "size": result.get("size"),
            "created": result.get("createdDateTime"),
            "modified": result.get("lastModifiedDateTime"),
            "download_url": result.get("@microsoft.graph.downloadUrl"),
        }

    def _chunked_upload(
        self, local_path: str, destination_path: str, file_size: int
    ) -> Dict[str, Any]:
        """Internal method for chunked upload (>= 4MB)"""
        # Create upload session
        encoded_path = quote(destination_path, safe="/")
        endpoint = f"/me/drive/root:/{encoded_path}:/createUploadSession"

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
                        "download_url": result.get("@microsoft.graph.downloadUrl"),
                    }

        # This shouldn't happen, but just in case
        raise OneDriveAPIError("Upload completed but no response received")

    def download_file_wrapper(self, remote_path: str, local_path: Optional[str] = None) -> Any:
        def download_file(item_id: Optional[str] = None, path: Optional[str] = None) -> bytes:
            if item_id:
                endpoint = f"/me/drive/items/{item_id}/content"
            elif path:
                encoded_path = quote(path, safe="/")
                endpoint = f"/me/drive/root:/{encoded_path}:/content"
            else:
                raise ValueError("Either item_id or path must be provided")

            response = self._make_request("GET", endpoint)
            return response.content

        if not self._is_authenticated():
            raise OneDriveAuthenticationError("Not authenticated")

        try:
            # Try to download by path first, then by ID
            if remote_path.startswith("/"):
                content = download_file(path=remote_path)
            else:
                content = download_file(item_id=remote_path)

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
        def move_item(item_id: str, new_parent_id: str, new_name: Optional[str] = None) -> Any:
            move_data = {"parentReference": {"id": new_parent_id}}

            if new_name:
                move_data["name"] = new_name  # type: ignore

            response = self._make_request("PATCH", f"/me/drive/items/{item_id}", json=move_data)
            return response.json()

        if not self._is_authenticated():
            raise OneDriveAuthenticationError("Not authenticated")

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

            # Perform move
            result = move_item(source_item["id"], dest_item["id"], new_name)

            return {
                "success": True,
                "new_id": result["id"],
                "new_name": result["name"],
                "new_path": result.get("parentReference", {}).get("path", "")
                + "/"
                + result["name"],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_item_wrapper(self, file_path: str) -> Any:
        def delete_item(item_id: Optional[str] = None, path: Optional[str] = None) -> bool:
            if item_id:
                endpoint = f"/me/drive/items/{item_id}"
            elif path:
                encoded_path = quote(path, safe="/")
                endpoint = f"/me/drive/root:/{encoded_path}"
            else:
                raise ValueError("Either item_id or path must be provided")

            response = self._make_request("DELETE", endpoint)
            return response.status_code == 204

        if not self._is_authenticated():
            raise OneDriveAuthenticationError("Not authenticated")

        try:
            if file_path.startswith("/"):
                success = delete_item(path=file_path)
            else:
                success = delete_item(item_id=file_path)

            return {"success": success}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_folder(self, folder_path: str, force: bool = False) -> Any:
        if not self._is_authenticated():
            raise OneDriveAuthenticationError("Not authenticated")

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
            success = self.delete_item_wrapper(folder_item["id"])
            return {"success": success}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _rename_item(self, item_id: str, new_name: str) -> Any:
        rename_data = {"name": new_name}
        response = self._make_request("PATCH", f"/me/drive/items/{item_id}", json=rename_data)
        return response.json()

    def rename_file(self, file_path: str, new_name: str) -> Any:
        if not self._is_authenticated():
            raise OneDriveAuthenticationError("Not authenticated")

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
            result = self._rename_item(file_item["id"], new_name)

            return {
                "success": True,
                "file_id": result["id"],
                "old_name": file_item["name"],
                "new_name": result["name"],
                "new_path": result.get("parentReference", {}).get("path", "")
                + "/"
                + result["name"],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def rename_folder(self, folder_path: str, new_name: str) -> Any:
        if not self._is_authenticated():
            raise OneDriveAuthenticationError("Not authenticated")

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
            result = self._rename_item(folder_item["id"], new_name)

            return {
                "success": True,
                "folder_id": result["id"],
                "old_name": folder_item["name"],
                "new_name": result["name"],
                "new_path": result.get("parentReference", {}).get("path", "")
                + "/"
                + result["name"],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _update_item_metadata(self, item_id: str, metadata: Dict[str, Any]) -> Any:
        # Filter metadata to only include allowed fields
        allowed_fields = ["name", "description"]
        filtered_metadata = {k: v for k, v in metadata.items() if k in allowed_fields}

        response = self._make_request("PATCH", f"/me/drive/items/{item_id}", json=filtered_metadata)
        return response.json()

    def update_file_metadata(
        self, file_path: str, description: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self._is_authenticated():
            raise OneDriveAuthenticationError("Not authenticated")

        try:
            # Get file info first
            if file_path.startswith("/"):
                file_item = self.get_item_by_path(file_path)
            else:
                file_item = self.get_item_by_id(file_path)

            # Prepare metadata update
            metadata = {}
            if description is not None:
                metadata["description"] = description

            if not metadata:
                return {"success": False, "error": "No metadata provided to update"}

            # Update metadata
            result = self._update_item_metadata(file_item["id"], metadata)

            return {
                "success": True,
                "file_id": result["id"],
                "name": result["name"],
                "description": result.get("description", ""),
                "updated": result["lastModifiedDateTime"],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_folder_metadata(self, folder_path: str, description: Optional[str] = None) -> Any:
        if not self._is_authenticated():
            raise OneDriveAuthenticationError("Not authenticated")

        try:
            # Get folder info first
            if folder_path.startswith("/"):
                folder_item = self.get_item_by_path(folder_path)
            else:
                folder_item = self.get_item_by_id(folder_path)

            # Verify it's a folder
            if "folder" not in folder_item:
                return {"success": False, "error": "Item is not a folder"}

            if description is None:
                return {"success": False, "error": "No description provided to update"}

            # Update metadata
            metadata = {"description": description}
            result = self._update_item_metadata(folder_item["id"], metadata)

            return {
                "success": True,
                "folder_id": result["id"],
                "name": result["name"],
                "description": result.get("description", ""),
                "updated": result["lastModifiedDateTime"],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_files(self, query: str, folder_path: Optional[str] = None) -> Any:
        def search_items(query: str, parent_id: Optional[str] = None) -> Any:
            if parent_id:
                endpoint = f"/me/drive/items/{parent_id}/search(q='{query}')"
            else:
                endpoint = f"/me/drive/root/search(q='{query}')"

            response = self._make_request("GET", endpoint)
            return response.json().get("value", [])

        if not self._is_authenticated():
            raise OneDriveAuthenticationError("Not authenticated")

        try:
            if folder_path:
                # Get folder ID first
                folder_item = self.get_item_by_path(folder_path)
                items = search_items(query, folder_item["id"])
            else:
                items = search_items(query)

            results = []
            for item in items:
                results.append(
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "path": item.get("parentReference", {}).get("path", "")
                        + "/"
                        + item["name"],
                        "size": item.get("size", 0),
                        "type": "folder" if "folder" in item else "file",
                        "modified": item["lastModifiedDateTime"],
                    }
                )

            return {"success": True, "results": results, "count": len(results)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_file_info(self, file_path: str) -> Any:
        if not self._is_authenticated():
            raise OneDriveAuthenticationError("Not authenticated")

        try:
            if file_path.startswith("/"):
                item = self.get_item_by_path(file_path)
            else:
                item = self.get_item_by_id(file_path)

            return {
                "success": True,
                "id": item["id"],
                "name": item["name"],
                "size": item.get("size", 0),
                "type": "folder" if "folder" in item else "file",
                "created": item["createdDateTime"],
                "modified": item["lastModifiedDateTime"],
                "path": item.get("parentReference", {}).get("path", "") + "/" + item["name"],
                "download_url": item.get("@microsoft.graph.downloadUrl"),
                "web_url": item.get("webUrl"),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_sharing_link(
        self, file_path: str, link_type: str = "view", scope: str = "anonymous"
    ) -> Any:
        def get_sharing_link(
            item_id: str, link_type: str = "view", scope: str = "anonymous"
        ) -> Any:
            link_data = {
                "type": link_type,  # view, edit
                "scope": scope,  # anonymous, organization
            }

            response = self._make_request(
                "POST", f"/me/drive/items/{item_id}/createLink", json=link_data
            )
            response_result = response.json()
            return {
                "success": True,
                "link": response_result["link"]["webUrl"],
                "type": response_result["link"]["type"],
                "scope": response_result["link"]["scope"],
            }

        if not self._is_authenticated():
            raise OneDriveAuthenticationError("Not authenticated")

        try:
            if file_path.startswith("/"):
                item = self.get_item_by_path(file_path)
                file_id = item["id"]
            else:
                file_id = file_path
            return get_sharing_link(file_id, link_type, scope)

        except Exception as e:
            return {"success": False, "error": str(e)}
