import os
import base64
from io import BytesIO
import time
import asyncio

import logging

logging.basicConfig(level=logging.INFO)
log = logging.info
from pathlib import Path
import shutil
from sanic import Sanic, response
from sanic_cors import CORS


DIR_PATH = os.path.dirname(os.path.realpath(__file__))

DEBUG = int(os.environ.get("DEBUG", 1))
STATIC_PATH = f"{DIR_PATH}/static"
VOYEUR_HOSTNAME = os.environ.get("FUZZY_HOSTNAME", "http://127.0.0.1:5666")

print("hostname", VOYEUR_HOSTNAME)
INDEX_HTML = (
    open(STATIC_PATH + "/index.html").read().replace("HOSTNAME", VOYEUR_HOSTNAME)
)

app = Sanic()
CORS(app)

#app.static("/static", STATIC_PATH)

headers = {
    "Cache-Control": "max-age=5, public"
}

async def run_drawing():
    while True:
        log("Started drawing")
        await asyncio.sleep(10)

        process = await asyncio.create_subprocess_exec(
            "python","python_drawing.py", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        log("DRAWING EXITED!!!, drawing exited")
        log(stderr)


app.add_task(run_drawing())

@app.middleware('response')
async def custom_banner(request, response):
    response.headers.update(headers)

@app.middleware('request')
async def custom_banner(request):
    request.headers.update(headers)

@app.route('/static/images/thumbnail.jpg')
async def handle_request(request):
    return await response.file(f'{STATIC_PATH}/images/thumbnail.jpg')

@app.route('/static/images/debug.jpg')
async def handle_request(request):
    return await response.file(f'{STATIC_PATH}/images/debug.jpg')

@app.route("/")
def home(request):
    return response.html(INDEX_HTML)

def sanic_main():
    try:
        app.run(host="0.0.0.0", port=80, debug=DEBUG)
    except:
        logging.exception("error")
        pass


if __name__ == "__main__":

    sanic_main()