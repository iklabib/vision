import requests 
import db
import re
import json
from requests.auth import HTTPDigestAuth

url = "http://10.19.99.10/cgi-bin/eventManager.cgi?action=attach&codes=[All]"
username = "admin"
password = "admincctv1"

def parse_event_body(body):
    event = {}
    parts = re.findall(r'(\w+)=({.*?}|[^;]+)', body)
    for key, value in parts:
        value = value.strip()
        if value.startswith('{') and value.endswith('}'):
            try:
                event[key] = json.loads(value)
            except Exception:
                event[key] = value
        else:
            event[key] = value
    return event

def invoke():
    auth = HTTPDigestAuth(username, password)
    with requests.get(url, auth=auth, stream=True) as response:
            content_type = response.headers.get('Content-Type', '')
            boundary = None
            if "boundary=" in content_type:
                boundary = content_type.split("boundary=")[-1].strip()
                if boundary.startswith('"') and boundary.endswith('"'):
                    boundary = boundary[1:-1]
            if not boundary:
                raise ValueError("Couldn't find boundary in Content-Type header")

            boundary = "--" + boundary
            buffer = ""

            for chunk in response.iter_content(chunk_size=1024):
                if not chunk:
                    continue
                buffer += chunk.decode(errors="ignore")
                while boundary in buffer:
                    part, buffer = buffer.split(boundary, 1)
                    if part.strip():
                        if "\r\n\r\n" in part:
                            headers_part, body = part.split("\r\n\r\n", 1)
                            body = body.strip()
                            parsed_event = parse_event_body(body)

                            # Insert based on Code
                            code = parsed_event.get('Code')
                            if code == 'VideoMotionInfo':
                                db.insert_video_motion_info(parsed_event)
                            elif code == 'VideoMotion':
                                db.insert_video_motion(parsed_event)
                            elif code == 'NewFile':
                                db.insert_new_file_event(parsed_event)