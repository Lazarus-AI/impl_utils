from unittest import mock

from lazarus_implementation_tools.sync.firebase.client import FirebaseStorageManager


class FirebaseMockMixin:
    blob_configs = [{"name": "/blob1", "generate_signed_url": "http://blob.com/blob1"}]

    def mock_blob(self, blob_config):
        blob = mock.Mock()
        blob.name = blob_config.get("name")
        blob.generate_signed_url.return_value = blob_config.get("generate_signed_url")
        return blob

    def get_mock_blobs(self, blob_configs=None):
        if blob_configs is None:
            blob_configs = self.blob_configs
        mock_blobs = []
        for blob_config in blob_configs:
            mock_blobs.append(self.mock_blob(blob_config))
        return mock_blobs


class TestFirebaseClient(FirebaseMockMixin):
    @mock.patch("firebase_admin.credentials.Certificate")
    @mock.patch("firebase_admin.storage.bucket")
    def test_list_all_files_in_path(self, mock_bucket, mock_credentials):
        mock_bucket.list_blobs.return_value = self.get_mock_blobs()

        client = FirebaseStorageManager(storage_url="fake_url.com")
        client.bucket = mock_bucket

        blobs = client.list_all_files_in_path("/")
        assert len(blobs) == 1
        for blob in blobs:
            assert blob == "blob1"

    @mock.patch("firebase_admin.credentials.Certificate")
    @mock.patch("firebase_admin.storage.bucket")
    def test_list_all_files_in_path(self, mock_bucket, mock_credentials):
        client = FirebaseStorageManager(storage_url="fake_url.com")
        blob = self.mock_blob({"name": "/file.pdf", "generate_signed_url": "http://blob.com/blob1"})
        assert not client.is_folder(blob)

        blob = self.mock_blob({"name": "/folder/", "generate_signed_url": "http://blob.com/blob1"})
        assert client.is_folder(blob)
