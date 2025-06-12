import json
import nanoid
import psycopg2
from psycopg2.extras import Json
from parse import EventNotificationAlert

server_name = "10.19.101.42"
port = 5000
database_name = 'DB_CCTV_SYS'
username = 'dbcctv'
password = 'B3basM3ngumpulkanD4taCctv!!!'

def update_vmd():
    with psycopg2.connect(
        host=server_name,
        port=port,
        database=database_name,
        user=username,
        password=password,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("CALL update_vmd_stats()")

def save_event(event: EventNotificationAlert):
    with psycopg2.connect(
        host=server_name,
        port=port,
        database=database_name,
        user=username,
        password=password,
    ) as conn:
        with conn.cursor() as cur:
            insert_query = """
                INSERT INTO event_notifications
                (id, ip_address, date_time, event_type, event_state, event_description, channel_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                nanoid.generate(size=10),
                event.ipAddress,
                event.dateTime,
                event.eventType,
                event.eventState,
                event.eventDescription,
                event.channelName
            )
            cur.execute(insert_query, values)
            conn.commit()

def insert_dahua(event):
    pk = nanoid.generate(size=10)
    data = event.get('data', {})
    event_type = data.get('Event', None)
    file_path = data.get('File', None)
    storage_point = data.get('StoragePoint', None)

    with psycopg2.connect(
        host=server_name,
        port=port,
        database=database_name,
        user=username,
        password=password,
    ) as conn:
        conn.cursor().execute("""
            INSERT INTO public.events(
                id, event_type, file_path, storage_point
            ) VALUES (%s, %s, %s, %s, %s)
        """, (pk, event_type, file_path, storage_point, ))
        return pk
    
def insert_raw(event: dict):
    with psycopg2.connect(
        host=server_name,
        port=port,
        database=database_name,
        user=username,
        password=password,
    ) as conn:
        conn.cursor().execute("INSERT INTO public.raw_events (id, event) VALUES (%s, %s)", (nanoid.generate(size=10), Json(event)))

def get_ips():
    with psycopg2.connect(
        host=server_name,
        port=port,
        database=database_name,
        user=username,
        password=password,
    ) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ipv4, brand FROM public.camera_ips")
        return cursor.fetchall()