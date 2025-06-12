import os
import sys
import tempfile
import time

here = os.path.dirname(__file__)
dir_path = os.path.join(os.path.dirname(here), "src")
os.chdir(dir_path)
sys.path.append(dir_path)

from lazarus_implementation_tools.sync.microsoft.utils import OneDriveUtils

CLIENT_ID = os.environ.get("ONE_DRIVE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ONE_DRIVE_CLIENT_SECRET")
TENANT_ID = os.environ.get("ONE_DRIVE_TENANT_ID")
REDIRECT_URI = os.environ.get("ONE_DRIVE_REDIRECT_URI")


class OneDriveTestSuite:
    """Comprehensive test suite for OneDrive utilities"""

    def __init__(self):
        self.onedrive = None
        self.test_files_created = []
        self.test_folders_created = []
        print("OneDrive Utilities Test Suite")
        print("=" * 50)

    def normalize_path(self, path):
        """Normalize OneDrive paths to the expected format. (makes life easier) Converts '/drive/root:/filename.txt' to '/filename.txt'"""
        if not path:
            return path

        # If it's a Microsoft Graph API path format
        if path.startswith("/drive/root:/"):
            # Extract the actual path part
            normalized = path.replace("/drive/root:", "")
            if not normalized.startswith("/"):
                normalized = "/" + normalized
            return normalized
        elif path.startswith("drive/root:/"):
            normalized = path.replace("drive/root:", "")
            if not normalized.startswith("/"):
                normalized = "/" + normalized
            return normalized
        else:
            # Already in correct format
            return path

    def setup_authentication(self):
        """Setup authentication with OneDrive"""
        print("Setting up authentication...")

        try:
            # Initialize OneDrive utils
            self.onedrive = OneDriveUtils(CLIENT_ID, CLIENT_SECRET, TENANT_ID)

            # Get authorization URL - user needs to visit this
            auth_url = self.onedrive.client.msal_app.get_authorization_request_url(
                scopes=["https://graph.microsoft.com/Files.ReadWrite"], redirect_uri=REDIRECT_URI
            )

            print(f"Please visit this URL to authorize the application:")
            print(f"{auth_url}")
            print(f"After authorizing, you'll be redirected to: {REDIRECT_URI}")
            print(f"Copy the 'code' parameter from the URL and paste it below.")

            # Get authorization code from user
            auth_code = input("Enter the authorization code: ").strip()

            if not auth_code:
                print("No authorization code provided!")
                return False

            # Authenticate
            success = self.onedrive.authenticate(auth_code, REDIRECT_URI)

            if success:
                print("Authentication successful!")
                return True
            else:
                print("Authentication failed!")
                return False

        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def test_file_upload(self):
        """Test file upload functionality"""
        print("Testing file upload...")

        try:
            # Create a temporary test file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                test_content = f"Test file created at {time.strftime('%Y-%m-%d %H:%M:%S')}\nThis is line 2\nThis is line 3"
                f.write(test_content)
                temp_file_path = f.name

            # Upload the file
            remote_path = "/test_upload.txt"
            result = self.onedrive.upload_file(temp_file_path, remote_path)

            # Clean up temp file
            os.unlink(temp_file_path)

            if result.get("success"):
                print(f"File uploaded successfully!")
                print(f"   Remote path: {remote_path}")
                print(f"   File ID: {result.get('file_id', 'N/A')}")
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
        print("Testing file download...")

        try:
            if not self.test_files_created:
                print("No uploaded files to test download")
                return False

            # Download the first uploaded file
            remote_path = self.test_files_created[0]

            local_path = "../onedrive_output_folder/onedrive_file.txt"
            result = self.onedrive.download_file(remote_path, local_path)

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
        print("Testing folder operations...")

        try:
            # Create a test folder
            folder_name = "test_folder"
            result = self.onedrive.create_folder(folder_name)

            if result.get("success"):
                print(f"Folder created successfully!")
                print(f"   Folder: {folder_name}")
                print(f"   Folder ID: {result.get('folder_id', 'N/A')}")
                self.test_folders_created.append(f"/{folder_name}")

                # Test uploading a file to the folder
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                    f.write("This file is inside a folder!")
                    temp_file_path = f.name

                folder_file_path = f"/{folder_name}/folder_file.txt"
                upload_result = self.onedrive.upload_file(temp_file_path, folder_file_path)
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
        print("Testing file listing...")

        try:
            # List root directory
            result = self.onedrive.list_files("/")

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

            result = self.onedrive.rename_file(original_path, new_name)

            if result.get("success"):
                print(f"File renamed successfully!")
                print(f"   Old name: {result.get('old_name', 'N/A')}")
                print(f"   New name: {result.get('new_name', 'N/A')}")

                # Update our tracking with the correct new path
                new_path = result.get("new_path")
                if new_path:
                    self.test_files_created[0] = new_path
                    print(f"   Updated tracking path: {new_path}")
                else:
                    # Fallback: construct the path manually
                    self.test_files_created[0] = f"/{new_name}"
                    print(f"   Fallback tracking path: /{new_name}")

                # Test folder rename if we have folders
                if self.test_folders_created:
                    folder_path = self.test_folders_created[0]
                    folder_result = self.onedrive.rename_folder(folder_path, "renamed_test_folder")

                    if folder_result.get("success"):
                        print(f"Folder renamed successfully!")
                        print(f"   Old name: {folder_result.get('old_name', 'N/A')}")
                        print(f"   New name: {folder_result.get('new_name', 'N/A')}")

                        # Update our tracking
                        new_folder_path = folder_result.get("new_path")
                        if new_folder_path:
                            self.test_folders_created[0] = new_folder_path
                        else:
                            self.test_folders_created[0] = "/renamed_test_folder"

                return True
            else:
                print(f"Rename failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"Rename test failed: {e}")
            return False

    def test_metadata_operations(self):
        """Test metadata update functionality"""
        print("Testing metadata operations...")

        try:
            if not self.test_files_created:
                print("No files to test metadata update")
                return False

            # Test file metadata update
            file_path = self.test_files_created[0]
            file_path = self.normalize_path(file_path)
            description = f"File metadata updated"

            result = self.onedrive.update_file_metadata(file_path, description)

            if result.get("success"):
                print(f"File metadata updated successfully!")
                print(f"   Description: {result.get('description', 'N/A')}")

                # Test folder metadata update if we have folders
                if self.test_folders_created:
                    folder_path = self.test_folders_created[0]
                    folder_description = "Folder metadata updated"

                    folder_result = self.onedrive.update_folder_metadata(
                        folder_path, folder_description
                    )

                    if folder_result.get("success"):
                        print(f"Folder metadata updated successfully!")
                        print(f"   Description: {folder_result.get('description', 'N/A')}")

                return True
            else:
                print(f"Metadata update failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"Metadata test failed: {e}")
            return False

    def test_search_functionality(self):
        """Test search functionality"""
        print("Testing search functionality...")

        try:
            # Search for test files
            result = self.onedrive.search_files("test")

            if result.get("success"):
                results = result.get("results", [])
                print(f"Search completed successfully!")
                print(f"   Found {len(results)} items matching 'test'")

                # Show some results
                for i, item in enumerate(results[:3]):  # Show first 3 results
                    print(f"   {i+1}. {item.get('name', 'N/A')} - {item.get('type', 'N/A')}")

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

            file_path = self.test_files_created[0]
            file_path = self.normalize_path(file_path)
            result = self.onedrive.get_file_info(file_path)

            if result.get("success"):
                print(f"File info retrieved successfully!")
                print(f"   Name: {result.get('name', 'N/A')}")
                print(f"   Size: {result.get('size', 'N/A')} bytes")
                print(f"   Created: {result.get('created', 'N/A')}")
                print(f"   Modified: {result.get('modified', 'N/A')}")
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

            file_path = self.test_files_created[0]
            file_path = self.normalize_path(file_path)
            result = self.onedrive.create_sharing_link(file_path, "view", "anonymous")

            if result.get("success"):
                print(f"Sharing link created successfully!")
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
            result = self.onedrive.move_file(
                "/renamed_test_file.txt", "/renamed_test_folder", "moved_renamed_test_file.txt"
            )
            if result.get("success"):
                print(
                    "renamed_test_file.txt moved successfully to renamed_test_folder and renamed to moved_renamed_test_file.txt"
                )
                return True
            else:
                print(f"renamed_test_file.txt failed to move, error: {result["error"]}")
                return False
        except Exception as e:
            print(f"Delete test failed: {e}")
            return False

    def test_delete_operations(self):
        """Test delete functionality"""
        print("Testing delete operations...")

        try:
            deleted_count = 0

            file_path = "/renamed_test_folder/folder_file.txt"
            result = self.onedrive.delete_file(file_path)
            if result.get("success"):
                print(f"Deleted file: {file_path}")
                deleted_count += 1
            else:
                print(f"Failed to delete file {file_path}: {result.get('error', 'Unknown error')}")

            folder_path = "/renamed_test_folder"
            result = self.onedrive.delete_folder(folder_path, force=True)
            if result.get("success"):
                print(f"Deleted folder: {folder_path}")
                deleted_count += 1
            else:
                print(
                    f"Failed to delete folder {folder_path}: {result.get('error', 'Unknown error')}"
                )

            print(f"Cleanup completed! Deleted {deleted_count} items.")
            return True

        except Exception as e:
            print(f"Delete test failed: {e}")
            return False

    def run_all_tests(self):
        """Run the complete test suite"""
        print("Starting comprehensive test suite...")

        # Authentication
        if not self.setup_authentication():
            print("Cannot proceed without authentication")
            return

        # Run all tests
        tests = [
            ("File Upload", self.test_file_upload),  # good
            ("File Download", self.test_file_download),  # bad
            ("Folder Operations", self.test_folder_operations),  # good
            ("File Listing", self.test_list_files),  # good
            ("Rename Operations", self.test_rename_operations),  # good
            ("Metadata Operations", self.test_metadata_operations),  # good
            ("Search Functionality", self.test_search_functionality),  # good
            ("File Info Retrieval", self.test_file_info),  # good
            ("Sharing Links", self.test_sharing_links),  # good
            ("Move Files", self.move_file),  # bad
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
                    print(f"{test_name} - PASSED")
                else:
                    print(f"{test_name} - FAILED")
            except Exception as e:
                print(f"{test_name} - ERROR: {e}")

            time.sleep(5)  # so you can see the results in onedrive.

        # Cleanup
        print(f"\n{'='*50}")
        print(f"Running cleanup...")
        print(f"{'='*50}")
        self.test_delete_operations()  # bad

        # Final results
        print(f"\n{'='*50}")
        print(f"TEST RESULTS")
        print(f"{'='*50}")
        print(f"Passed: {passed_tests}/{total_tests}")
        print(f"Failed: {total_tests - passed_tests}/{total_tests}")

        if passed_tests == total_tests:
            print("All tests passed! Your OneDrive integration is working perfectly!")
        else:
            print("Some tests failed. Check the output above for details.")


def main():
    """Main function to run the test suite"""
    if not CLIENT_ID or CLIENT_ID == "your-client-id-here":
        print("Please update CLIENT_ID with your actual Azure application ID")
        print("See the setup guide for instructions on getting these values")
        return

    if not CLIENT_SECRET or CLIENT_SECRET == "your-client-secret-here":
        print("Please update CLIENT_SECRET with your actual Azure client secret")
        print("See the setup guide for instructions on getting these values")
        return

    # Run the test suite
    test_suite = OneDriveTestSuite()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main()
