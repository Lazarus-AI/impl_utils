import os
import sys
import tempfile
import time

here = os.path.dirname(__file__)
dir_path = os.path.join(os.path.dirname(here), "src")
os.chdir(dir_path)
sys.path.append(dir_path)

from sync.gdrive.utils import GoogleDriveUtils

CREDENTIALS_PATH = os.environ.get("GOOGLE_DRIVE_CREDENTIALS_PATH", "credentials.json")
TOKEN_PATH = os.environ.get("GOOGLE_DRIVE_TOKEN_PATH", "token.json")


class GoogleDriveTestSuite:
    """Comprehensive test suite for Google Drive utilities"""

    def __init__(self):
        self.gdrive = None
        self.test_files_created = []
        self.test_folders_created = []
        print("Google Drive Utilities Test Suite")
        print("=" * 50)

    def normalize_path(self, path):
        """Normalize Google Drive paths to the expected format. For Google Drive, this mainly handles file IDs vs URLs."""
        if not path:
            return path

        # If it's a Google Drive URL, extract the file ID
        if path.startswith("https://drive.google.com"):
            if "/d/" in path:
                # File URL format
                return path.split("/d/")[1].split("/")[0]
            elif "/folders/" in path:
                # Folder URL format
                return path.split("/folders/")[1].split("/")[0]

        return path

    def setup_authentication(self):
        """Setup authentication with Google Drive"""
        print("Setting up authentication...")

        try:
            # Initialize Google Drive utils
            self.gdrive = GoogleDriveUtils(CREDENTIALS_PATH, TOKEN_PATH)

            # Test authentication
            auth_result = self.gdrive.authenticate()

            if auth_result:
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
            remote_path = "/"  # Upload to root
            result = self.gdrive.upload_file(temp_file_path, remote_path)

            # Clean up temp file
            os.unlink(temp_file_path)

            if result.get("success"):
                print(f"File uploaded successfully!")
                print(f"   File ID: {result.get('file_id', 'N/A')}")
                print(f"   Name: {result.get('name', 'N/A')}")
                file_id = result.get("file_id")
                if file_id:
                    self.test_files_created.append(file_id)
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
            file_id = self.test_files_created[0]

            local_path = "../gdrive_output_folder/gdrive_file.txt"
            result = self.gdrive.download_file(file_id, local_path)

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
            result = self.gdrive.create_folder(folder_name)

            if result.get("success"):
                print(f"Folder created successfully!")
                print(f"   Folder: {folder_name}")
                print(f"   Folder ID: {result.get('folder_id', 'N/A')}")
                folder_id = result.get("folder_id")
                if folder_id:
                    self.test_folders_created.append(folder_id)

                # Test uploading a file to the folder
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                    f.write("This file is inside a folder!")
                    temp_file_path = f.name

                upload_result = self.gdrive.upload_file(temp_file_path, folder_id)
                os.unlink(temp_file_path)

                if upload_result.get("success"):
                    print(f"File uploaded to folder successfully!")
                    file_id = upload_result.get("file_id")
                    if file_id:
                        self.test_files_created.append(file_id)

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
            result = self.gdrive.list_files("/")

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

    def test_search_functionality(self):
        """Test search functionality"""
        print("Testing search functionality...")

        try:
            # Search for test files
            result = self.gdrive.search_files("test")

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

            file_id = self.test_files_created[0]
            result = self.gdrive.get_file_info(file_id)

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

            file_id = self.test_files_created[0]
            result = self.gdrive.create_sharing_link(file_id, "view", "anonymous")

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

    def test_delete_operations(self):
        """Test delete functionality"""
        print("Testing delete operations...")

        try:
            deleted_count = 0

            # Delete test files
            for file_id in self.test_files_created:
                result = self.gdrive.delete_file(file_id)
                if result.get("success"):
                    print(f"Deleted file: {file_id}")
                    deleted_count += 1
                else:
                    print(
                        f"Failed to delete file {file_id}: {result.get('error', 'Unknown error')}"
                    )

            # Delete test folders
            for folder_id in self.test_folders_created:
                result = self.gdrive.delete_folder(folder_id, force=True)
                if result.get("success"):
                    print(f"Deleted folder: {folder_id}")
                    deleted_count += 1
                else:
                    print(
                        f"Failed to delete folder {folder_id}: {result.get('error', 'Unknown error')}"
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
            ("File Upload", self.test_file_upload),
            ("File Download", self.test_file_download),
            ("Folder Operations", self.test_folder_operations),
            ("File Listing", self.test_list_files),
            ("Search Functionality", self.test_search_functionality),
            ("File Info Retrieval", self.test_file_info),
            ("Sharing Links", self.test_sharing_links),
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

            time.sleep(5)  # Brief pause between tests (so I can see what's new)

        # Cleanup
        print(f"\n{'='*50}")
        print(f"Running cleanup...")
        print(f"{'='*50}")

        time.sleep(10)
        self.test_delete_operations()

        # Final results
        print(f"\n{'='*50}")
        print(f"TEST RESULTS")
        print(f"{'='*50}")
        print(f"Passed: {passed_tests}/{total_tests}")
        print(f"Failed: {total_tests - passed_tests}/{total_tests}")

        if passed_tests == total_tests:
            print("All tests passed! Your Google Drive integration is working perfectly!")
        else:
            print("Some tests failed. Check the output above for details.")


def main():
    """Main function to run the test suite"""
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"Please ensure credentials file exists at: {CREDENTIALS_PATH}")
        print("See the Google Drive API setup guide for instructions on getting credentials")
        return

    # Run the test suite
    test_suite = GoogleDriveTestSuite()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main()
