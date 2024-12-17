import subprocess
import base64
import struct
import textwrap

class VMP:
    def __init__(self, path: str):
        self.keygen_path = path

    def generate_key(self, username: str, telegramid: int, expiredate: int) -> str:
        telegramid_bytes = struct.pack(">Q", telegramid)
        expiredate_bytes = struct.pack(">Q", expiredate)

        user_data_bytes = telegramid_bytes + expiredate_bytes
        user_data = base64.b64encode(user_data_bytes).decode('utf-8')

        command = [
            'node', self.keygen_path,
            '--userName', username,
            '--userData', user_data
        ]

        result = subprocess.run(command, capture_output=True, text=True)
        return '\n'.join(textwrap.wrap(result.stdout.strip(), 76))
