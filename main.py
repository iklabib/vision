import multiprocessing
import dahua
import uvicorn
import db
from stream import alert_stream
from parse import parse_event_notification, EventNotificationAlert

url = "http://10.19.120.219/ISAPI/Event/notification/alertStream"
username = "admin"
password = "@dmincctv1"

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
    p = multiprocessing.Process(target=dahua.invoke)
    p.start()
    uvicorn.run(app, host='0.0.0.0', port=5000, reload=False)