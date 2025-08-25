import http.server
import os
import socketserver
import sys
import tempfile
import threading
import time
import urllib.parse
import webbrowser
from datetime import datetime

# Add path to your implementation tools
here = os.path.dirname(__file__)
dir_path = os.path.join(os.path.dirname(here), "src")
os.chdir(dir_path)
sys.path.append(dir_path)

from lazarus_implementation_tools.sync.microsoft.utils import O365EmailUtils

# Load credentials from environment or config
CLIENT_ID = os.environ.get("O365_EMAIL_CLIENT_ID")
CLIENT_SECRET = os.environ.get("O365_EMAIL_CLIENT_SECRET")
TENANT_ID = os.environ.get("O365_EMAIL_TENANT_ID")
REDIRECT_URI = os.environ.get("O365_EMAIL_REDIRECT_URI", "http://localhost:3000/auth/callback")
USER_PRINCIPAL_NAME = os.environ.get("O365_EMAIL_USER_PRINCIPAL_NAME", "<insert email here>")
EMAIL_TEST_ADDRESS = os.environ.get("O365_EMAIL_TEST_ADDRESS", "<insert email here>")


class O365EmailTestSuite:
    """Comprehensive test suite for Office 365 Email utilities"""

    def __init__(self):
        self.email_utils = None
        self.test_emails_sent = []
        self.test_folders_created = []
        print("Office 365 Email Utilities Test Suite")
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
        """Setup authentication with Office 365"""
        print("Setting up authentication...")

        try:
            # Initialize O365 email utils
            self.email_utils = O365EmailUtils(
                CLIENT_ID, CLIENT_SECRET, TENANT_ID, USER_PRINCIPAL_NAME
            )

            # Get authorization URL
            auth_url = self.email_utils.client.msal_app.get_authorization_request_url(
                scopes=[
                    "https://graph.microsoft.com/Mail.ReadWrite",
                    "https://graph.microsoft.com/Mail.Send",
                    "https://graph.microsoft.com/Mail.ReadWrite.Shared",
                    "https://graph.microsoft.com/MailboxSettings.Read",
                    "https://graph.microsoft.com/User.Read",
                ],
                redirect_uri=REDIRECT_URI,
                prompt="consent",
            )

            auth_code = self.get_auth_code(auth_url, REDIRECT_URI)

            if not auth_code:
                print("No authorization code provided!")
                return False

            success = self.email_utils.authenticate(auth_code, REDIRECT_URI)

            if success:
                print("Authentication successful!")
                print(f"Connected to mailbox: {USER_PRINCIPAL_NAME}")
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

    def test_get_inbox_emails(self):
        """Test retrieving inbox emails"""
        print("Testing inbox email retrieval...")

        try:
            result = self.email_utils.get_inbox_emails(
                limit=10, unread_only=False, include_attachments=False
            )

            if result.get("success"):
                print(f"Retrieved {result['count']} emails from inbox")

                # Show first few emails
                for i, email in enumerate(result["messages"][:3], 1):
                    print(f"   {i}. {email['subject'][:50]}...")
                    print(f"      From: {email['from_email']}")
                    print(f"      Date: {email['received_datetime']}")

                return True
            else:
                print(f"Failed to retrieve emails: {result.get('error')}")
                return False

        except Exception as e:
            print(f"Test failed: {e}")
            return False

    def test_send_email(self):
        """Test sending an email"""
        print("Testing email sending...")

        try:
            # Send test email to self
            result = self.email_utils.send_email(
                to_recipients=[USER_PRINCIPAL_NAME],
                subject=f"Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                body="This is a test email sent from the O365 Email Utils test suite.\n\nThis email can be safely deleted.",
                is_html=False,
            )

            if result.get("success"):
                print(f"Email sent successfully!")
                self.test_emails_sent.append(result)
                return True
            else:
                print(f"Failed to send email: {result.get('error')}")
                return False

        except Exception as e:
            print(f"Test failed: {e}")
            return False

    def test_send_email_to_another_address(self):
        """Test sending an email"""
        print("Testing email sending...")

        try:
            # Send test email to self
            result = self.email_utils.send_email(
                to_recipients=[EMAIL_TEST_ADDRESS],
                subject=f"Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                body="This is a test email sent from the O365 Email Utils test suite.\n\nThis email can be safely deleted.",
                is_html=False,
            )

            if result.get("success"):
                print(f"Email sent successfully!")
                self.test_emails_sent.append(result)
                return True
            else:
                print(f"Failed to send email: {result.get('error')}")
                return False

        except Exception as e:
            print(f"Test failed: {e}")
            return False

    def test_send_email_with_attachment(self):
        """Test sending email with attachment"""
        print("Testing email with attachment...")

        try:
            # Create a temporary test file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write("This is a test attachment file.\n")
                f.write(f"Created at: {datetime.now()}\n")
                temp_file = f.name

            result = self.email_utils.send_email(
                to_recipients=[USER_PRINCIPAL_NAME],
                subject=f"Test Email with Attachment - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                body="<h3>Test Email</h3><p>This email contains an attachment.</p>",
                is_html=True,
                attachments=[{"name": "test_attachment.txt", "path": temp_file}],
            )

            # Clean up temp file
            os.unlink(temp_file)

            if result.get("success"):
                print(f"Email with attachment sent successfully!")
                return True
            else:
                print(f"Failed to send email: {result.get('error')}")
                return False

        except Exception as e:
            print(f"Test failed: {e}")
            return False

    def test_search_emails(self):
        """Test email search functionality"""
        print("Testing email search...")

        try:
            result = self.email_utils.search_emails(query="test", limit=10)

            if result.get("success"):
                print(f"Search completed, found {result['count']} emails")

                for i, email in enumerate(result["messages"][:3], 1):
                    print(f"   {i}. {email['subject'][:50]}...")

                return True
            else:
                print(f"Search failed: {result.get('error')}")
                return False

        except Exception as e:
            print(f"Test failed: {e}")
            return False

    def test_email_statistics(self):
        """Test email statistics"""
        print("Testing email statistics...")

        try:
            result = self.email_utils.get_email_statistics(days_back=7)

            if result.get("success"):
                print(f"Statistics for last 7 days:")
                print(f"   Inbox: {result['inbox']['total']} emails")
                print(f"   Unread: {result['inbox']['unread']} emails")
                print(f"   Daily average (inbox): {result['inbox']['daily_average']:.1f}")

                if result["top_senders"]:
                    print(
                        f"   Top sender: {result['top_senders'][0]['email']} ({result['top_senders'][0]['count']} emails)"
                    )

                return True
            else:
                print(f"Failed to get statistics: {result.get('error')}")
                return False

        except Exception as e:
            print(f"Test failed: {e}")
            return False

    def test_mark_emails_as_read(self):
        """Test marking emails as read"""
        print("Testing mark as read functionality...")

        try:
            # Get unread emails
            emails_result = self.email_utils.get_inbox_emails(limit=5, unread_only=True)

            if not emails_result.get("success") or not emails_result["messages"]:
                print("   No unread emails to test with")
                return True

            # Mark first email as read
            message_id = emails_result["messages"][0]["id"]
            result = self.email_utils.mark_emails_as_read([message_id])

            if result.get("success"):
                print(f"Marked {result['marked_read']} email(s) as read")
                return True
            else:
                print(f"Failed to mark emails as read")
                return False

        except Exception as e:
            print(f"Test failed: {e}")
            return False

    def test_store_emails_with_attachments(self):
        """Test storing emails with attachments"""
        print("Testing email storage with attachments...")

        try:
            result = self.email_utils.store_emails_with_attachments(
                limit=10, unread_only=False, days_back=7, mark_as_read=False
            )

            if result.get("success"):
                print(f"Email storage completed:")
                print(f"   Total emails: {result['total_emails']}")
                print(f"   Stored: {result['stored']}")
                print(f"   Failed: {result['failed']}")
                print(f"   Storage path: {result['storage_path']}")
                return True
            else:
                print(f"Storage failed: {result.get('error')}")
                return False

        except Exception as e:
            print(f"Test failed: {e}")
            return False

    def run_all_tests(self):
        """Run the complete test suite"""
        print("Starting comprehensive Office 365 Email test suite...")
        print(f"Target mailbox: {USER_PRINCIPAL_NAME}")

        # Authentication
        if not self.setup_authentication():
            print("Cannot proceed without authentication")
            return

        # Get mailbox info
        info = self.email_utils.get_mailbox_info()
        if info.get("success"):
            print(f"Connected to: {info['user_principal_name']}")

        # Run all tests
        tests = [
            ("Get Inbox Emails", self.test_get_inbox_emails),
            ("Send Email", self.test_send_email),
            ("Send Email to Another Address", self.test_send_email_to_another_address),
            ("Send Email with Attachment", self.test_send_email_with_attachment),
            ("Search Emails", self.test_search_emails),
            ("Email Statistics", self.test_email_statistics),
            ("Mark Emails as Read", self.test_mark_emails_as_read),
            ("Store Emails with Attachments", self.test_store_emails_with_attachments),
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

            time.sleep(7)  # Brief pause between tests

        # Final results
        print(f"\n{'='*50}")
        print(f"TEST RESULTS")
        print(f"{'='*50}")
        print(f"Passed: {passed_tests}/{total_tests}")
        print(f"Failed: {total_tests - passed_tests}/{total_tests}")

        if passed_tests == total_tests:
            print("✅ All tests passed! Your O365 Email integration is working perfectly!")
        else:
            print("Some tests failed. Check the output above for details.")


def main():
    """Main function to run the test suite"""
    if not CLIENT_ID or CLIENT_ID == "your-client-id-here":
        print("Please update O365_EMAIL_CLIENT_ID with your actual Azure application ID")
        print("See the setup guide for instructions on getting these values")
        return

    if not CLIENT_SECRET or CLIENT_SECRET == "your-client-secret-here":
        print("Please update O365_EMAIL_CLIENT_SECRET with your actual Azure client secret")
        return

    if not USER_PRINCIPAL_NAME:
        print("Please update O365_EMAIL_USER_PRINCIPAL_NAME with the target email address")
        return

    # Run the test suite
    test_suite = O365EmailTestSuite()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main()
