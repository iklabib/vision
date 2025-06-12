import multiprocessing
import dahua
import uvicorn
import db
from stream import alert_stream
from parse import parse_event_notification, EventNotificationAlert

##################################
# Hook Alarm CCTV Hikvision      #
# Sekaligus Stream Request Dahua #
##################################

username = "admin"
password = "@dmincctv1"

##################################
# Daftarkan ini di Alarm Hikvision
# 10.19.101.118/alarm
##################################
host = '0.0.0.0' # biarin, jangan diganti!
port = 5_000 # boleh diganti

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.api_route('/alarm', methods=['POST', 'PUT'])
async def alarm(request: Request):
    form_data = await request.form()
    if len(form_data) > 0:
        data = form_data.get('MoveDetection.xml')
        content = await data.read()
        dt = parse_event_notification(content)
        if dt.eventType != "videoloss":
            db.save_event(dt)

    return PlainTextResponse('OK', status_code=200)

if __name__ == "__main__":
    # disini jalanin request  ke kamera Dahua
    dahua_ips = [ip for ip, brand in db.get_ips() if brand == "DAHUA"]
    with multiprocessing.Pool() as pool:
        results = [pool.apply_async(dahua.invoke, (ip,)) for ip in dahua_ips]
    
    # kalau ini server hook Hikvision
    uvicorn.run(app, host=host, port=port, reload=False)