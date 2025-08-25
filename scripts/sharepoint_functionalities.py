import http.server
import os
import socketserver
import sys
import tempfile
import threading
import time
import urllib.parse
import webbrowser

here = os.path.dirname(__file__)
dir_path = os.path.join(os.path.dirname(here), "src")
os.chdir(dir_path)
sys.path.append(dir_path)

from lazarus_implementation_tools.sync.microsoft.utils import SharePointUtils

CLIENT_ID = os.environ.get("SHAREPOINT_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SHAREPOINT_CLIENT_SECRET")
TENANT_ID = os.environ.get("SHAREPOINT_TENANT_ID")
REDIRECT_URI = os.environ.get("SHAREPOINT_REDIRECT_URI")
SITE_NAME = os.environ.get("SHAREPOINT_SITE_NAME")


class SharePointTestSuite:
    """Comprehensive test suite for SharePoint utilities"""

    def __init__(self):
        self.sharepoint = None
        self.test_files_created = []
        self.test_folders_created = []
        self.test_list_items = []
        print("SharePoint Utilities Test Suite")
        print("=" * 50)

    def get_auth_code(self, auth_url, redirect_uri):
        """Open browser, start local server, and capture OAuth2 code automatically."""

        parsed = urllib.parse.urlparse(redirect_uri)
        port = parsed.port or 80

        auth_code_container = {}

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                query = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(query)
                if "code" in params:
                    auth_code_container["code"] = params["code"][0]
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"Authorization complete. You can close this tab.")
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Authorization failed. No code found.")

            def log_message(self, *args):
                return  # silence default logging

        # Start temporary local server
        httpd = socketserver.TCPServer(("localhost", port), Handler)
        thread = threading.Thread(target=httpd.serve_forever)
        thread.daemon = True
        thread.start()

        print(f"Opening browser to: {auth_url}")
        webbrowser.open(auth_url)

        # Wait until code is captured
        print("Waiting for authorization...")
        while "code" not in auth_code_container:
            pass

        # Shutdown server
        httpd.shutdown()
        thread.join()

        return auth_code_container["code"]

    def setup_authentication(self):
        """Setup authentication with SharePoint"""
        print("Setting up authentication...")

        try:
            # Initialize SharePoint utils
            self.sharepoint = SharePointUtils(CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_NAME)

            # Get authorization URL - user needs to visit this
            auth_url = self.sharepoint.client.msal_app.get_authorization_request_url(
                scopes=[
                    # "https://graph.microsoft.com/Sites.ReadWrite.All",
                    # "https://graph.microsoft.com/Files.ReadWrite.All",
                    "https://graph.microsoft.com/Files.ReadWrite",
                    "https://graph.microsoft.com/User.Read",
                ],
                redirect_uri=REDIRECT_URI,
                prompt="consent",
            )

            auth_code = self.get_auth_code(auth_url, REDIRECT_URI)

            if not auth_code:
                print("No authorization code provided!")
                return False

            # Authenticate
            success = self.sharepoint.authenticate(auth_code, REDIRECT_URI)

            if success:
                print("Authentication successful!")
                print(f"Connected to SharePoint site: {SITE_NAME}")
                return True
            else:
                print("Authentication failed!")
                return False

        except Exception as e:
            if "Address already in use" in str(e):
                return True
            else:
                print(f"Authentication error: {e}")
                return False

    def test_file_upload(self):
        """Test file upload functionality"""
        print("Testing file upload to SharePoint Documents library...")

        try:
            # Create a temporary test file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                test_content = f"SharePoint test file created at {time.strftime('%Y-%m-%d %H:%M:%S')}\nThis is line 2\nThis is line 3"
                f.write(test_content)
                temp_file_path = f.name

            # Upload the file to Documents library
            remote_path = "/Documents/test_upload.txt"
            result = self.sharepoint.upload_file(temp_file_path, remote_path)

            # Clean up temp file
            os.unlink(temp_file_path)

            if result.get("success"):
                print(f"File uploaded successfully!")
                print(f"   Remote path: {remote_path}")
                print(f"   File ID: {result.get('file_id', 'N/A')}")
                print(f"   Web URL: {result.get('web_url', 'N/A')[:50]}...")
                self.test_files_created.append(remote_path)
                return True
            else:
                print(f"Upload failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"Upload test failed: {e}")
            return False

    def test_file_download(self):
        """Test file download functionality"""
        print("Testing file download from SharePoint...")

        try:
            if not self.test_files_created:
                print("No uploaded files to test download")
                return False

            # Download the first uploaded file
            remote_path = self.test_files_created[0]

            local_path = "../sharepoint_output_folder/sharepoint_file.txt"
            result = self.sharepoint.download_file(remote_path, local_path)

            if result.get("success"):
                print(f"File downloaded successfully!")
                print(f"   Local path: {local_path}")
                print(f"   Size: {result.get('size', 'N/A')} bytes")

                # Verify content
                if os.path.exists(local_path):
                    with open(local_path, "r") as f:
                        content = f.read()
                    print(f"   Content preview: {content[:50]}...")

                return True
            else:
                print(f"Download failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"Download test failed: {e}")
            return False

    def test_folder_operations(self):
        """Test folder creation and listing"""
        print("Testing folder operations in SharePoint Documents library...")

        try:
            # Create a test folder in Documents library
            folder_name = "test_folder"
            result = self.sharepoint.create_folder(folder_name, "/Documents")

            if result.get("success"):
                print(f"Folder created successfully!")
                print(f"   Folder: {folder_name}")
                print(f"   Folder ID: {result.get('folder_id', 'N/A')}")
                self.test_folders_created.append(f"/Documents/{folder_name}")

                # Test uploading a file to the folder
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                    f.write("This file is inside a SharePoint folder!")
                    temp_file_path = f.name

                folder_file_path = f"/Documents/{folder_name}/folder_file.txt"
                upload_result = self.sharepoint.upload_file(temp_file_path, folder_file_path)
                os.unlink(temp_file_path)

                if upload_result.get("success"):
                    print(f"File uploaded to folder successfully!")
                    self.test_files_created.append(folder_file_path)

                return True
            else:
                print(f"Folder creation failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"Folder operations test failed: {e}")
            return False

    def test_list_files(self):
        """Test file listing functionality"""
        print("Testing file listing in SharePoint Documents library...")

        try:
            # List Documents library
            result = self.sharepoint.list_files("/Documents")

            if result.get("success"):
                files = result.get("files", [])
                folders = result.get("folders", [])

                print(f"Directory listing successful!")
                print(f"   Files: {len(files)}")
                print(f"   Folders: {len(folders)}")

                # Show some files
                if files:
                    print("   Recent files:")
                    for file in files[:3]:  # Show first 3 files
                        print(
                            f"      - {file.get('name', 'N/A')} ({file.get('size', 'N/A')} bytes)"
                        )

                # Show some folders
                if folders:
                    print("   Folders:")
                    for folder in folders[:3]:  # Show first 3 folders
                        print(f"      - {folder.get('name', 'N/A')}")

                return True
            else:
                print(f"File listing failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"File listing test failed: {e}")
            return False

    def test_rename_operations(self):
        """Test rename functionality"""
        print("Testing rename operations...")

        try:
            if not self.test_files_created:
                print("⚠️ No files to test rename")
                return False

            # Test file rename
            original_path = self.test_files_created[0]
            new_name = "renamed_test_file.txt"

            result = self.sharepoint.rename_file(original_path, new_name)

            if result.get("success"):
                print(f"File renamed successfully!")
                print(f"   Old name: {result.get('old_name', 'N/A')}")
                print(f"   New name: {result.get('new_name', 'N/A')}")

                # Update our tracking
                new_path = result.get("new_path")
                if new_path:
                    self.test_files_created[0] = new_path
                else:
                    # Construct path manually
                    parent_path = "/".join(original_path.split("/")[:-1])
                    self.test_files_created[0] = f"{parent_path}/{new_name}"

                # Test folder rename if we have folders
                if self.test_folders_created:
                    folder_path = self.test_folders_created[0]
                    folder_result = self.sharepoint.rename_folder(
                        folder_path, "renamed_test_folder"
                    )

                    if folder_result.get("success"):
                        print(f"Folder renamed successfully!")
                        print(f"   Old name: {folder_result.get('old_name', 'N/A')}")
                        print(f"   New name: {folder_result.get('new_name', 'N/A')}")

                        # Update our tracking
                        new_folder_path = folder_result.get("new_path")
                        if new_folder_path:
                            self.test_folders_created[0] = new_folder_path
                        else:
                            self.test_folders_created[0] = "/Documents/renamed_test_folder"

                return True
            else:
                print(f"Rename failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"Rename test failed: {e}")
            return False

    def test_search_functionality(self):
        """Test search functionality"""
        print("Testing search functionality in SharePoint...")

        try:
            # Search for test files
            result = self.sharepoint.search_files("test")

            if result.get("success"):
                results = result.get("results", [])
                print(f"Search completed successfully!")
                print(f"   Found {len(results)} items matching 'test'")

                # Show some results
                for i, item in enumerate(results[:3]):  # Show first 3 results
                    print(f"   {i+1}. {item.get('name', 'N/A')} - {item.get('type', 'N/A')}")
                    print(f"      Path: {item.get('path', 'N/A')}")

                return True
            else:
                print(f"Search failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"Search test failed: {e}")
            return False

    def test_file_info(self):
        """Test get file info functionality"""
        print("Testing file info retrieval...")

        try:
            if not self.test_files_created:
                print("No files to get info for")
                return False

            result = self.sharepoint.get_file_info("/Documents/renamed_test_file.txt")

            if result.get("success"):
                print(f"File info retrieved successfully!")
                print(f"   Name: {result.get('name', 'N/A')}")
                print(f"   Size: {result.get('size', 'N/A')} bytes")
                print(f"   Created: {result.get('created', 'N/A')}")
                print(f"   Modified: {result.get('modified', 'N/A')}")
                print(f"   Created by: {result.get('created_by', 'N/A')}")
                print(f"   Web URL: {result.get('web_url', 'N/A')[:50]}...")

                return True
            else:
                print(f"Get file info failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"File info test failed: {e}")
            return False

    def test_sharing_links(self):
        """Test sharing link creation"""
        print("Testing sharing link creation...")

        try:
            if not self.test_files_created:
                print("No files to create sharing links for")
                return False

            result = self.sharepoint.create_sharing_link(
                "/Documents/renamed_test_file.txt", "view", "organization"
            )

            if result.get("success"):
                print(
                    f"Sharing link created successfully! (KEEP IN MIND YOU NEED TO CLICK THIS BEFORE THE DELETE OPERATIONS RUN.)"
                )
                print(f"   Link: {result.get('link', 'N/A')}")
                print(f"   Type: {result.get('type', 'N/A')}")
                print(f"   Scope: {result.get('scope', 'N/A')}")

                return True
            else:
                print(f"Sharing link creation failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"Sharing link test failed: {e}")
            return False

    def move_file(self):
        """Test move files"""
        try:
            source_path = "/Documents/renamed_test_file.txt"
            dest_folder = "/Documents/renamed_test_folder"
            new_name = "moved_renamed_test_file.txt"

            result = self.sharepoint.move_file(source_path, dest_folder, new_name)

            if result.get("success"):
                print(f"File moved successfully!")
                print(f"   From: {source_path}")
                print(f"   To: {dest_folder}/{new_name}")
                # Update tracking
                self.test_files_created[0] = f"{dest_folder}/{new_name}"
                return True
            else:
                print(f"File move failed: {result.get('error')}")
                return False

        except Exception as e:
            print(f"Move test failed: {e}")
            return False

    def test_delete_operations(self):
        """Test delete functionality"""
        print("Testing delete operations...")

        try:
            deleted_count = 0

            # Delete test files
            file_path = "/Documents/renamed_test_folder/moved_renamed_test_file.txt"
            result = self.sharepoint.delete_file(file_path)
            if result.get("success"):
                print(f"Deleted file: {file_path}")
                deleted_count += 1
            else:
                print(f"Failed to delete file {file_path}: {result.get('error')}")

            # Delete test folders
            folder_path = "/Documents/renamed_test_folder"
            result = self.sharepoint.delete_folder(folder_path, force=True)
            if result.get("success"):
                print(f"Deleted folder: {folder_path}")
                deleted_count += 1
            else:
                print(f"Failed to delete folder {folder_path}: {result.get('error')}")

            print(f"Cleanup completed! Deleted {deleted_count} items.")
            return True

        except Exception as e:
            print(f"Delete test failed: {e}")
            return False

    def run_all_tests(self):
        """Run the complete test suite"""
        print("Starting comprehensive SharePoint test suite...")
        print(f"Target site: {SITE_NAME}")

        # Authentication
        if not self.setup_authentication():
            print("Cannot proceed without authentication")
            return

        # Run all tests
        tests = [
            ("File Upload", self.test_file_upload),
            ("File Download", self.test_file_download),
            ("Folder Operations", self.test_folder_operations),
            ("File Listing", self.test_list_files),
            ("Rename Operations", self.test_rename_operations),
            ("Search Functionality", self.test_search_functionality),
            ("File Info Retrieval", self.test_file_info),
            ("Sharing Links", self.test_sharing_links),
            ("Move Files", self.move_file),
        ]

        passed_tests = 0
        total_tests = len(tests)

        for test_name, test_func in tests:
            print(f"\n{'='*50}")
            print(f"Running: {test_name}")
            print(f"{'='*50}")

            try:
                if test_func():
                    passed_tests += 1
                    print(f"✓ {test_name} - PASSED")
                else:
                    print(f"✗ {test_name} - FAILED")
            except Exception as e:
                print(f"✗ {test_name} - ERROR: {e}")

            time.sleep(5)  # Brief pause between tests

        # Cleanup
        print(f"\n{'='*50}")
        print(f"Running cleanup...")
        time.sleep(10)
        print(f"{'='*50}")
        self.test_delete_operations()

        # Final results
        print(f"\n{'='*50}")
        print(f"TEST RESULTS")
        print(f"{'='*50}")
        print(f"Passed: {passed_tests}/{total_tests}")
        print(f"Failed: {total_tests - passed_tests}/{total_tests}")

        if passed_tests == total_tests:
            print("✅ All tests passed! Your SharePoint integration is working perfectly!")
        else:
            print("⚠️ Some tests failed. Check the output above for details.")


def main():
    """Main function to run the test suite"""
    if not CLIENT_ID or CLIENT_ID == "your-client-id-here":
        print("Please update SHAREPOINT_CLIENT_ID with your actual Azure application ID")
        print("See the setup guide for instructions on getting these values")
        return

    if not CLIENT_SECRET or CLIENT_SECRET == "your-client-secret-here":
        print("Please update SHAREPOINT_CLIENT_SECRET with your actual Azure client secret")
        print("See the setup guide for instructions on getting these values")
        return

    if not SITE_NAME:
        print("Please update SHAREPOINT_SITE_NAME with your SharePoint site name")
        return

    # Run the test suite
    test_suite = SharePointTestSuite()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main()
