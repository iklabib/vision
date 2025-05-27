import json
import nanoid
import psycopg2
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
            cur.execute("UPDATE public.vmd_stats SET status = 0")

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
                (id, version, ip_address, ipv6_address, port_no, protocol, mac_address, channel_id, date_time,
                    active_post_count, event_type, event_state, event_description, channel_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                nanoid.generate(size=10),
                event.version,
                event.ipAddress,
                event.ipv6Address,
                event.portNo,
                event.protocol,
                event.macAddress,
                event.channelID,
                event.dateTime,
                event.activePostCount,
                event.eventType,
                event.eventState,
                event.eventDescription,
                event.channelName
            )
            cur.execute(insert_query, values)
            conn.commit()

def insert_video_motion_info(event):
    pk = nanoid.generate(size=10)
    with psycopg2.connect(
        host=server_name,
        port=port,
        database=database_name,
        user=username,
        password=password,
    ) as conn:
        conn.cursor().execute("""
            INSERT INTO dahua_cam.video_motion_info (id, action, event_index)
            VALUES (%s, %s, %s)
        """, (pk, event.get('action'), int(event.get('index'))))
        conn.commit()
        return pk

def insert_video_motion(event):
    # video_motion: id, action, event_index, ids[], region_names[]
    pk = nanoid.generate(size=10)
    data = event.get('data', {})
    ids = data.get('Id', [])
    region_names = data.get('RegionName', [])
    # Convert string lists to Python lists if needed (sometimes might be string)
    if isinstance(ids, str):
        ids = json.loads(ids)
    if isinstance(region_names, str):
        region_names = json.loads(region_names)
    # convert ids to int list
    ids = [int(i) for i in ids]
    region_names = [str(r) for r in region_names]

    with psycopg2.connect(
        host=server_name,
        port=port,
        database=database_name,
        user=username,
        password=password,
    ) as conn:
        conn.cursor().execute("""
            INSERT INTO dahua_cam.video_motion (id, action, event_index, ids, region_names)
            VALUES (%s, %s, %s, %s, %s)
        """, (pk, event.get('action'), int(event.get('index')), ids, region_names))
        conn.commit()
    return pk

def insert_new_file_event(event):
    # new_file_event: id, action, event_index, data_ids[], data_region_names[],
    # event_type, file_path, file_index, file_size, storage_point, created_at
    pk = nanoid.generate(size=10)
    data = event.get('data', {})
    inner_data = data.get('Data', {})
    data_ids = inner_data.get('Id', [])
    data_region_names = inner_data.get('RegionName', [])
    if isinstance(data_ids, str):
        data_ids = json.loads(data_ids)
    if isinstance(data_region_names, str):
        data_region_names = json.loads(data_region_names)
    data_ids = [int(i) for i in data_ids]
    data_region_names = [str(r) for r in data_region_names]

    event_type = data.get('Event')
    file_path = data.get('File')
    file_index = data.get('Index')
    file_size = data.get('Size')
    storage_point = data.get('StoragePoint')


    with psycopg2.connect(
        host=server_name,
        port=port,
        database=database_name,
        user=username,
        password=password,
    ) as conn:
        conn.cursor().execute("""
            INSERT INTO dahua_cam.new_file_event (
                id, action, event_index, data_ids, data_region_names,
                event_type, file_path, file_index, file_size, storage_point
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            pk, event.get('action'), int(event.get('index')), data_ids, data_region_names,
            event_type, file_path, file_index, file_size, storage_point
        ))
        return pk