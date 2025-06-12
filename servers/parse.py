from dataclasses import dataclass
from datetime import datetime
import xml.etree.ElementTree as ET

@dataclass
class EventNotificationAlert:
    version: str
    ipAddress: str
    ipv6Address: str
    portNo: int
    protocol: str
    macAddress: str
    channelID: int
    dateTime: datetime
    activePostCount: int
    eventType: str
    eventState: str
    eventDescription: str
    channelName: str

def parse_event_notification(xml_string: str) -> EventNotificationAlert:
    ns = {'ns': 'http://www.hikvision.com/ver20/XMLSchema'}
    root = ET.fromstring(xml_string)

    def get_text(tag):
        el = root.find(f'ns:{tag}', ns)
        return el.text if el is not None else None

    return EventNotificationAlert(
        version=root.attrib.get('version'),
        ipAddress=get_text('ipAddress'),
        ipv6Address=get_text('ipv6Address'),
        portNo=int(get_text('portNo')),
        protocol=get_text('protocol'),
        macAddress=get_text('macAddress'),
        channelID=int(get_text('channelID')),
        dateTime=datetime.fromisoformat(get_text('dateTime')),
        activePostCount=int(get_text('activePostCount')),
        eventType=get_text('eventType'),
        eventState=get_text('eventState'),
        eventDescription=get_text('eventDescription'),
        channelName=get_text('channelName'),
    )