import os
import uuid
import oss2
#pip3 install oss2


class OssUploader:
    def __init__(self, access_key_id: str, access_key_secret: str, endpoint: str, bucket_name: str):
        self.bucket_name = bucket_name
        self.endpoint = endpoint
        self.auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(self.auth, endpoint, bucket_name)

    def _generate_filename(self, original_filename: str) -> str:
        ext = original_filename.split('.')[-1]
        return f"{uuid.uuid4()}.{ext}"

    def upload_bytes(self, file_bytes: bytes, filename: str = None) -> str:
        oss_key = filename or self._generate_filename("file.bin")
        self.bucket.put_object(oss_key, file_bytes)
        return self._build_url(oss_key)

    def upload_fileobj(self, fileobj, filename: str = None) -> str:
        oss_key = filename or self._generate_filename("file.bin")
        self.bucket.put_object(oss_key, fileobj)
        return self._build_url(oss_key)

    def upload_local_file(self, local_path: str, oss_path: str = None) -> str:
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"本地文件不存在: {local_path}")
        with open(local_path, 'rb') as f:
            return self.upload_fileobj(f, oss_path or os.path.basename(local_path))

    def _build_url(self, oss_key: str) -> str:
        return f"https://{self.bucket_name}.{self.endpoint}/{oss_key}"
