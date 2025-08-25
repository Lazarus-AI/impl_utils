import base64
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import msal
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class O365EmailAuthenticationError(Exception):
    """Raised when authentication fails"""

    pass


class O365EmailAPIError(Exception):
    """Raised when API requests fail"""

    pass


class O365EmailRateLimitError(Exception):
    """Raised when rate limit is hit"""

    pass


class EmailStorage:
    """Handles organized storage of emails with metadata, body content, and attachments"""

    def __init__(self, base_storage_path: str = "stored_emails"):
        """Initialize email storage system

        Args:
            base_storage_path: Base directory for storing emails

        """
        if ".." not in base_storage_path:
            self.base_path = Path(f"../{base_storage_path}")  # gets sent to src folder by default.

        self.base_path.mkdir(exist_ok=True)

        self.index_file = self.base_path / "email_index.json"
        self.index = self._load_index()

        logger.info(f"Email storage initialized at: {self.base_path.absolute()}")

    def _load_index(self):
        """Load the master email index"""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    index_data = json.load(f)
                    if isinstance(index_data.get("processed_email_ids"), list):
                        index_data["processed_email_ids"] = set(index_data["processed_email_ids"])
                    return index_data
            except Exception as e:
                logger.warning(f"Could not load index file: {e}")

        return {
            "created": datetime.now().isoformat(),
            "total_emails": 0,
            "emails_by_date": {},
            "processed_email_ids": set(),
        }

    def _save_index(self):
        """Save the master email index"""
        try:
            index_copy = self.index.copy()
            index_copy["processed_email_ids"] = list(self.index["processed_email_ids"])

            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(index_copy, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save index: {e}")

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        import re

        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        filename = filename.strip(". ")
        filename = filename.rstrip()
        return filename[:100]

    def store_email(self, email_data: Dict[str, Any]) -> Optional[str]:
        """Store complete email with metadata, body, and attachments"""
        try:
            email_id = email_data.get("id")
            if email_id in self.index.get("processed_email_ids", set()):
                logger.info(f"Email {email_id} already processed, skipping")
                return None

            # Create folder structure
            received_dt = datetime.fromisoformat(
                email_data["received_datetime"].replace("Z", "+00:00")
            )
            date_str = received_dt.strftime("%Y-%m-%d")
            time_str = received_dt.strftime("%H-%M-%S")

            date_folder = self.base_path / date_str
            date_folder.mkdir(exist_ok=True)

            if date_str not in self.index["emails_by_date"]:
                self.index["emails_by_date"][date_str] = 0

            self.index["emails_by_date"][date_str] += 1
            email_counter = self.index["emails_by_date"][date_str]

            from_email = email_data.get("from_email", "unknown")
            clean_from = self._sanitize_filename(from_email.replace("@", "."))[:40]
            subject = email_data.get("subject", "No Subject")
            clean_subject = self._sanitize_filename(subject)[:25]

            folder_name = f"email_{email_counter:03d}_{time_str}_{clean_from}_{clean_subject}"
            email_folder = date_folder / folder_name
            email_folder.mkdir(exist_ok=True)

            # Store metadata
            metadata_file = email_folder / "metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(email_data, f, indent=2, ensure_ascii=False)

            # Store body
            body_content = email_data.get("body_content", "")
            if body_content:
                if email_data.get("body_content_type") == "HTML":
                    body_file = email_folder / "body.html"
                else:
                    body_file = email_folder / "body.txt"
                with open(body_file, "w", encoding="utf-8") as f:
                    f.write(body_content)

            # Store attachments
            attachments = email_data.get("attachments", [])
            if attachments:
                attachments_folder = email_folder / "attachments"
                attachments_folder.mkdir(exist_ok=True)

                for i, attachment in enumerate(attachments):
                    att_type = attachment.get("@odata.type", "").lower()

                    # Handle file attachments
                    if "fileattachment" in att_type and attachment.get("contentBytes"):
                        try:
                            content = base64.b64decode(attachment["contentBytes"])
                            safe_name = self._sanitize_filename(
                                attachment.get("name", f"attachment_{i+1}")
                            )

                            # Ensure unique filename
                            attachment_path = attachments_folder / safe_name
                            counter = 1
                            while attachment_path.exists():
                                name_parts = safe_name.rsplit(".", 1)
                                if len(name_parts) == 2:
                                    safe_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                                else:
                                    safe_name = f"{safe_name}_{counter}"
                                attachment_path = attachments_folder / safe_name
                                counter += 1

                            with open(attachment_path, "wb") as f:
                                f.write(content)

                            logger.info(f"Stored attachment: {safe_name}")

                        except Exception as e:
                            logger.error(
                                f"Failed to decode/store attachment {attachment.get('name')}: {e}"
                            )

                    # Handle item attachments (nested emails)
                    elif "ItemAttachment" in att_type:
                        logger.warning(
                            f"Skipping ItemAttachment (nested email): {attachment.get('name')}"
                        )

                    # Handle reference attachments (OneDrive/SharePoint links)
                    elif "ReferenceAttachment" in att_type:
                        logger.warning(
                            f"Skipping ReferenceAttachment (link): {attachment.get('name')}"
                        )

                    else:
                        logger.warning(
                            f"Unknown attachment type {att_type} for {attachment.get('name')}"
                        )

            self.index["total_emails"] += 1
            self.index["processed_email_ids"].add(email_id)
            self._save_index()

            logger.info(f"Email stored successfully: {email_folder.name}")
            return str(email_folder)

        except Exception as e:
            logger.error(f"Failed to store email: {e}")
            return None


class O365EmailClient:
    def __init__(
        self, client_id: str, client_secret: str, tenant_id: str, user_principal_name: str
    ):
        """Initialize Office 365 Email client

        Args:
            client_id: Azure AD application ID client_secret: Azure AD client secret
            tenant_id: Azure AD tenant ID user_principal_name: User's email address
            (e.g., user@company.com)

        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.user_principal_name = user_principal_name

        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.authenticated = False

        # Rate limiting
        self.last_request_time = None
        self.min_request_interval = 0.1  # 100ms between requests

        # MSAL app for authentication
        self.msal_app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
        )

        # Email folders
        self.folders = {}  # type: ignore
        self.inbox_id = None
        self.sent_id = None
        self.drafts_id = None
        self.deleted_id = None

        # Email storage
        self.email_storage = None

    def _is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self.authenticated and self.access_token is not None

    def authenticate_with_code(
        self, authorization_code: str, redirect_uri: str, scopes: List[str] = None
    ):
        """Authenticate using authorization code flow

        Args:
            authorization_code: OAuth authorization code redirect_uri: Redirect URI used
            in OAuth flow scopes: List of scopes to request

        """
        try:
            if scopes is None:
                scopes = [
                    "https://graph.microsoft.com/Mail.ReadWrite",
                    "https://graph.microsoft.com/Mail.ReadWrite.Shared",
                    "https://graph.microsoft.com/Mail.Send",
                    "https://graph.microsoft.com/Mail.Send.Shared",
                    "https://graph.microsoft.com/MailboxSettings.ReadWrite",
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

                # Initialize mailbox folders
                self._initialize_folders()

                return True
            else:
                error_msg = result.get("error_description", "Authentication failed")
                raise O365EmailAuthenticationError(f"Authentication failed: {error_msg}")

        except Exception as e:
            if "Address already in use" in str(e):
                return True
            raise O365EmailAuthenticationError(f"Authentication error: {str(e)}")

    def authenticate_app_only(self, scopes: List[str] = None):
        """Authenticate using client credentials flow (app-only access)

        Args:
            scopes: List of scopes to request

        """
        try:
            if scopes is None:
                scopes = ["https://graph.microsoft.com/.default"]

            result = self.msal_app.acquire_token_for_client(scopes=scopes)

            if "access_token" in result:
                self.access_token = result["access_token"]
                self.token_expires_at = time.time() + result.get("expires_in", 3600)
                self.authenticated = True

                # Initialize mailbox folders
                self._initialize_folders()

                return True
            else:
                error_msg = result.get("error_description", "Authentication failed")
                raise O365EmailAuthenticationError(f"Authentication failed: {error_msg}")

        except Exception as e:
            raise O365EmailAuthenticationError(f"Authentication error: {str(e)}")

    def _initialize_folders(self):
        """Initialize mailbox folder IDs"""
        try:
            response = self._make_request("GET", f"/users/{self.user_principal_name}/mailFolders")
            folders = response.json().get("value", [])

            for folder in folders:
                folder_name = folder.get("displayName", "").lower()
                folder_id = folder.get("id")

                self.folders[folder_name] = folder_id

                if folder_name == "inbox":
                    self.inbox_id = folder_id
                elif folder_name == "sent items":
                    self.sent_id = folder_id
                elif folder_name == "drafts":
                    self.drafts_id = folder_id
                elif folder_name == "deleted items":
                    self.deleted_id = folder_id

        except Exception as e:
            logger.warning(f"Could not initialize folders: {e}")

    def refresh_access_token(self):
        """Refresh the access token"""
        if not self.refresh_token:
            # Try app-only authentication
            return self.authenticate_app_only()

        try:
            result = self.msal_app.acquire_token_by_refresh_token(
                refresh_token=self.refresh_token,
                scopes=[
                    "https://graph.microsoft.com/Mail.ReadWrite",
                    "https://graph.microsoft.com/Mail.Send",
                ],
            )

            if "access_token" in result:
                self.access_token = result["access_token"]
                self.refresh_token = result.get("refresh_token", self.refresh_token)
                self.token_expires_at = time.time() + result.get("expires_in", 3600)
                return True
            else:
                raise O365EmailAuthenticationError("Token refresh failed")

        except Exception as e:
            raise O365EmailAuthenticationError(f"Token refresh error: {str(e)}")

    def _ensure_valid_token(self):
        """Ensure access token is valid"""
        if not self.access_token:
            raise O365EmailAuthenticationError("No access token available")

        if time.time() >= self.token_expires_at - 300:  # Refresh 5 minutes before expiry
            self.refresh_access_token()

    def _rate_limit(self):
        """Implement basic rate limiting"""
        if self.last_request_time:
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.min_request_interval:
                time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated request to Microsoft Graph API"""
        self._ensure_valid_token()
        self._rate_limit()

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
                raise O365EmailRateLimitError(f"Rate limited. Retry after {retry_after} seconds")

            # Handle other errors
            if not response.ok:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", {}).get(
                    "message", f"HTTP {response.status_code}"
                )
                raise O365EmailAPIError(f"API request failed: {error_msg}")

            return response

        except requests.RequestException as e:
            raise O365EmailAPIError(f"Request failed: {str(e)}")

    def get_messages(
        self,
        folder: str = "inbox",
        limit: int = 50,
        skip: int = 0,
        filter_query: Optional[str] = None,
        search_query: Optional[str] = None,
        order_by: str = "receivedDateTime desc",
        select_fields: Optional[List[str]] = None,
        expand_fields: Optional[List[str]] = None,
        include_attachments: bool = False,
    ) -> Dict[str, Any]:
        """Get messages from a folder

        Args:
            folder: Folder name or ID (default: "inbox") limit: Maximum number of
            messages to retrieve skip: Number of messages to skip (for pagination)
            filter_query: OData filter query search_query: Search query string order_by:
            Sort order select_fields: Fields to include in response expand_fields:
            Fields to expand include_attachments: Include attachment data

        Returns:
            Dict with messages and metadata

        """
        if not self._is_authenticated():
            raise O365EmailAuthenticationError("Not authenticated")

        try:
            # Determine folder ID
            if folder.lower() in self.folders:
                folder_id = self.folders[folder.lower()]
            elif folder == "inbox" and self.inbox_id:
                folder_id = self.inbox_id
            else:
                folder_id = folder  # Assume it's already an ID

            # Build endpoint
            endpoint = f"/users/{self.user_principal_name}/mailFolders/{folder_id}/messages"

            # Build query parameters
            params = {
                "$top": min(limit, 1000),
                "$skip": skip,
                "$orderby": order_by,
                "$count": "true",
            }

            # Add select fields
            if select_fields:
                params["$select"] = ",".join(select_fields)
            else:
                params["$select"] = (
                    "id,subject,bodyPreview,body,from,toRecipients,ccRecipients,bccRecipients,receivedDateTime,sentDateTime,hasAttachments,importance,isRead,isDraft,webLink,flag,categories,conversationId,conversationIndex"
                )

            # Add expand fields
            if expand_fields:
                params["$expand"] = ",".join(expand_fields)
            elif include_attachments:
                params["$expand"] = "attachments"
                params["$select"] += ",attachments"  # type: ignore

            # Add filter
            if filter_query:
                params["$filter"] = filter_query

            # Add search
            if search_query:
                params["$search"] = f'"{search_query}"'

            response = self._make_request("GET", endpoint, params=params)
            data = response.json()

            messages = []
            for msg in data.get("value", []):
                processed_msg = self._process_message(msg)
                if include_attachments and msg.get("hasAttachments"):
                    processed_msg["attachments"] = msg.get("attachments", [])
                messages.append(processed_msg)

            return {
                "success": True,
                "messages": messages,
                "count": len(messages),
                "total_count": data.get("@odata.count", len(messages)),
                "has_more": "@odata.nextLink" in data,
                "next_link": data.get("@odata.nextLink"),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_message(
        self,
        to_recipients: List[str],
        subject: str,
        body: str,
        cc_recipients: Optional[List[str]] = None,
        bcc_recipients: Optional[List[str]] = None,
        importance: str = "normal",
        is_html: bool = False,
        attachments: Optional[List[Dict]] = None,
        save_to_sent: bool = True,
        reply_to: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send an email message

        Args:
            to_recipients: List of recipient email addresses subject: Email subject
            body: Email body content cc_recipients: List of CC recipient emails
            bcc_recipients: List of BCC recipient emails importance: Message importance
            (low, normal, high) is_html: Whether body is HTML attachments: List of
            attachment dicts with 'name' and 'content' or 'path' save_to_sent: Save to
            sent folder reply_to: List of reply-to email addresses

        Returns:
            Result dict with success status

        """
        if not self._is_authenticated():
            raise O365EmailAuthenticationError("Not authenticated")

        try:
            # Build message
            message = {
                "subject": subject,
                "importance": importance,
                "body": {"contentType": "HTML" if is_html else "Text", "content": body},
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in to_recipients],
            }

            if cc_recipients:
                message["ccRecipients"] = [
                    {"emailAddress": {"address": addr}} for addr in cc_recipients
                ]

            if bcc_recipients:
                message["bccRecipients"] = [
                    {"emailAddress": {"address": addr}} for addr in bcc_recipients
                ]

            if reply_to:
                message["replyTo"] = [{"emailAddress": {"address": addr}} for addr in reply_to]

            # Add attachments
            if attachments:
                message["attachments"] = []
                for att in attachments:
                    if "path" in att:
                        # Read file from path
                        with open(att["path"], "rb") as f:
                            content = base64.b64encode(f.read()).decode()
                        name = att.get("name", os.path.basename(att["path"]))
                    else:
                        # Use provided content
                        content = att["content"]
                        if isinstance(content, bytes):
                            content = base64.b64encode(content).decode()
                        name = att["name"]

                    message["attachments"].append(  # type: ignore[attr-defined]
                        {
                            "@odata.type": "#microsoft.graph.fileAttachment",
                            "name": name,
                            "contentBytes": content,
                        }
                    )

            # Send message
            send_data = {"message": message, "saveToSentItems": save_to_sent}

            response = self._make_request(
                "POST", f"/users/{self.user_principal_name}/sendMail", json=send_data
            )

            return {"success": True, "message": "Email sent successfully"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_message(self, message_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a message

        Args:
            message_id: Message ID updates: Updates to apply (isRead, categories, flag,
            etc.)

        Returns:
            Updated message data

        """
        if not self._is_authenticated():
            raise O365EmailAuthenticationError("Not authenticated")

        try:
            response = self._make_request(
                "PATCH", f"/users/{self.user_principal_name}/messages/{message_id}", json=updates
            )

            return {"success": True, "message": self._process_message(response.json())}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def mark_as_read(self, message_id: str, is_read: bool = True) -> Dict[str, Any]:
        """Mark a message as read or unread

        Args:
            message_id: Message ID is_read: Mark as read (True) or unread (False)

        Returns:
            Result dict

        """
        return self.update_message(message_id, {"isRead": is_read})

    def search_messages(
        self, query: str, folder: Optional[str] = None, limit: int = 50
    ) -> Dict[str, Any]:
        """Search for messages

        Args:
            query: Search query folder: Folder to search in (None = all folders) limit:
            Maximum results

        Returns:
            Search results

        """
        if folder:
            return self.get_messages(folder=folder, search_query=query, limit=limit)
        else:
            # Search across all folders
            if not self._is_authenticated():
                raise O365EmailAuthenticationError("Not authenticated")

            try:
                endpoint = f"/users/{self.user_principal_name}/messages"
                params = {
                    "$search": f'"{query}"',
                    "$top": min(limit, 250),
                    "$select": "id,subject,bodyPreview,from,receivedDateTime,hasAttachments,importance,isRead",
                }

                response = self._make_request("GET", endpoint, params=params)
                data = response.json()

                messages = [self._process_message(msg) for msg in data.get("value", [])]

                return {"success": True, "messages": messages, "count": len(messages)}

            except Exception as e:
                return {"success": False, "error": str(e)}

    def get_mailbox_settings(self) -> Dict[str, Any]:
        """Get mailbox settings

        Returns:
            Mailbox settings

        """
        if not self._is_authenticated():
            raise O365EmailAuthenticationError("Not authenticated")

        try:
            response = self._make_request(
                "GET", f"/users/{self.user_principal_name}/mailboxSettings"
            )
            settings = response.json()

            return {"success": True, "settings": settings}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw message data into cleaner format"""
        processed = {
            "id": message.get("id"),
            "conversation_id": message.get("conversationId"),
            "subject": message.get("subject", ""),
            "body_preview": message.get("bodyPreview", ""),
            "body_content": message.get("body", {}).get("content", ""),
            "body_content_type": message.get("body", {}).get("contentType", "text"),
            "from_email": "",
            "from_name": "",
            "received_datetime": message.get("receivedDateTime"),
            "sent_datetime": message.get("sentDateTime"),
            "is_read": message.get("isRead", False),
            "is_draft": message.get("isDraft", False),
            "has_attachments": message.get("hasAttachments", False),
            "importance": message.get("importance", "normal"),
            "web_link": message.get("webLink", ""),
            "categories": message.get("categories", []),
            "flag": message.get("flag", {}),
            "to_recipients": [],
            "cc_recipients": [],
            "bcc_recipients": [],
        }

        # Process from field
        if message.get("from"):
            from_data = message["from"].get("emailAddress", {})
            processed["from_email"] = from_data.get("address", "")
            processed["from_name"] = from_data.get("name", "")

        # Process recipients
        for recipient in message.get("toRecipients", []):
            processed["to_recipients"].append(
                {
                    "email": recipient.get("emailAddress", {}).get("address", ""),
                    "name": recipient.get("emailAddress", {}).get("name", ""),
                }
            )

        for recipient in message.get("ccRecipients", []):
            processed["cc_recipients"].append(
                {
                    "email": recipient.get("emailAddress", {}).get("address", ""),
                    "name": recipient.get("emailAddress", {}).get("name", ""),
                }
            )

        for recipient in message.get("bccRecipients", []):
            processed["bcc_recipients"].append(
                {
                    "email": recipient.get("emailAddress", {}).get("address", ""),
                    "name": recipient.get("emailAddress", {}).get("name", ""),
                }
            )

        return processed

    # ============= HIGH-LEVEL UTILITY METHODS =============

    def init_email_storage(self, storage_path: str = "stored_emails"):
        """Initialize email storage for this client"""
        self.email_storage = EmailStorage(storage_path)  # type: ignore

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
        filter_query = None
        filters = []

        if unread_only:
            filters.append("isRead eq false")

        if days_back:
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            filters.append(f"receivedDateTime ge {cutoff_date}")

        if filters:
            filter_query = " and ".join(filters)

        return self.get_messages(
            folder="inbox",
            limit=limit,
            filter_query=filter_query,
            include_attachments=include_attachments,
        )

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
        return self.send_message(
            to_recipients=to_recipients,
            subject=subject,
            body=body,
            cc_recipients=cc_recipients,
            bcc_recipients=bcc_recipients,
            attachments=attachments,
            is_html=is_html,
        )

    def mark_emails_as_read(self, message_ids: List[str]) -> Dict[str, Any]:
        """Mark multiple emails as read

        Args:
            message_ids: List of message IDs

        Returns:
            Result dict with success/failure counts

        """
        success_count = 0
        failed_count = 0

        for msg_id in message_ids:
            result = self.mark_as_read(msg_id, is_read=True)
            if result["success"]:
                success_count += 1
            else:
                failed_count += 1

        return {
            "success": True,
            "marked_read": success_count,
            "failed": failed_count,
            "total": len(message_ids),
        }

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
        return self.search_messages(query, folder, limit)

    def store_emails_with_attachments(
        self,
        limit: int = 50,
        unread_only: bool = True,
        days_back: Optional[int] = None,
        mark_as_read_after: bool = False,
    ) -> Dict[str, Any]:
        """Store emails with attachments to local storage

        Args:
            limit: Number of emails to process unread_only: Only process unread emails
            days_back: Only process emails from last N days mark_as_read_after: Mark
            emails as read after storing

        Returns:
            Processing results

        """
        if not self.email_storage:
            self.email_storage = EmailStorage()  # type: ignore

        # Get emails
        emails_result = self.get_inbox_emails(
            limit=limit, unread_only=unread_only, include_attachments=True, days_back=days_back
        )

        if not emails_result["success"]:
            return emails_result

        emails = emails_result["messages"]
        stored_count = 0
        failed_count = 0
        marked_read_count = 0

        for email in emails:
            # Store email
            stored_path = self.email_storage.store_email(email)  # type: ignore

            if stored_path:
                stored_count += 1
                logger.info(f"Stored email: {email['subject']}")

                # Mark as read if requested
                if mark_as_read_after:
                    read_result = self.mark_as_read(email["id"], is_read=True)
                    if read_result["success"]:
                        marked_read_count += 1
            else:
                failed_count += 1

        return {
            "success": True,
            "total_emails": len(emails),
            "stored": stored_count,
            "failed": failed_count,
            "marked_read": marked_read_count,
            "storage_path": str(self.email_storage.base_path),  # type: ignore
        }

    def get_email_statistics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get email statistics

        Args:
            days_back: Number of days to analyze

        Returns:
            Email statistics

        """
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        # Get inbox stats
        inbox_result = self.get_messages(
            folder="inbox",
            filter_query=f"receivedDateTime ge {cutoff_date}",
            limit=999,
            select_fields=["id", "from", "receivedDateTime", "isRead", "hasAttachments"],
        )

        if not inbox_result["success"]:
            return {"success": False, "error": "Failed to get statistics"}

        inbox_messages = inbox_result["messages"]

        # Analyze inbox
        unread_count = sum(1 for msg in inbox_messages if not msg.get("is_read", False))
        with_attachments = sum(1 for msg in inbox_messages if msg.get("has_attachments", False))

        # Count by sender
        sender_counts = {}  # type: ignore
        for msg in inbox_messages:
            sender = msg.get("from_email", "unknown")
            sender_counts[sender] = sender_counts.get(sender, 0) + 1

        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "success": True,
            "period_days": days_back,
            "inbox": {
                "total": len(inbox_messages),
                "unread": unread_count,
                "with_attachments": with_attachments,
                "daily_average": len(inbox_messages) / days_back,
            },
            "top_senders": [{"email": email, "count": count} for email, count in top_senders],
        }

    def get_mailbox_info(self) -> Dict[str, Any]:
        """Get mailbox settings and information

        Returns:
            Mailbox information

        """
        settings = self.get_mailbox_settings()

        if settings["success"]:
            return {
                "success": True,
                "user_principal_name": self.user_principal_name,
                "settings": settings["settings"],
            }

        return {"success": False, "error": "Failed to get mailbox info"}
