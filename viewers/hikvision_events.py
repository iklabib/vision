import json
import select
import psycopg2
import connection

def hikvision_event_stream(poll_timeout: int = 5):
    channel_name: str = "hikvision_events"

    conf = connection.load('cctv')

    conn = None
    try:
        conn = psycopg2.connect(host=conf.host,
                                port=conf.port, 
                                dbname=conf.database,
                                user=conf.username,
                                password=conf.password)

        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        cursor = conn.cursor()
        cursor.execute(f"LISTEN {channel_name};")

        while True:
            # polling `poll_timeout` in seconds
            if select.select([conn], [], [], poll_timeout) == ([conn], [], []):
                conn.poll()
                while conn.notifies:
                    notification = conn.notifies.pop(0)
                    yield {
                        "channel": notification.channel,
                        "pid": notification.pid,
                        "payload": notification.payload
                    }

    except psycopg2.Error as e:
        print(f"Generator ERROR: Database connection or query failed: {e}")
    except Exception as e:
        print(f"Generator ERROR: An unexpected error occurred: {e}")
    finally:
        if conn:
            print("Generator: Closing PostgreSQL connection.")
            conn.close()

if __name__ == "__main__":
    try:
        for event_data in hikvision_event_stream():
            print(f"  PID: {event_data['pid']}")
            print(f"  Raw Payload: {event_data['payload']}")

            parsed_payload = json.loads(event_data['payload'])
            print(f"  Parsed JSON Payload: {json.dumps(parsed_payload, indent=2)}")

    except KeyboardInterrupt:
        print("\nListener stopped by user (Ctrl+C).")
    except Exception as e:
        print(f"An unexpected error occurred while consuming the stream: {e}")