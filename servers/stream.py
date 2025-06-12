from typing import Generator
from requests.auth import HTTPDigestAuth
import requests

def alert_stream(url, username, password) -> Generator[tuple[int, str | None], None, None]:
    with requests.get(url, auth=HTTPDigestAuth(username, password), stream=True) as response:
        if response.status_code != 200:
            yield (response.status_code, None)
            return
         
        buffer = ""
        for raw_line in response.iter_lines():
            if raw_line:
                try:
                    line = raw_line.decode("utf-8")
                    if not (str(line).startswith('<') and str(line).endswith('>')):
                        continue

                except UnicodeDecodeError:
                    continue

                buffer += line + "\n"

                if "</EventNotificationAlert>" in line:
                    event_text = buffer.strip()
                    yield (200, event_text)
                    buffer = ""