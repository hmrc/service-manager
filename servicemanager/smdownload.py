import requests
import time
import sys


def _report_hook(count, block_size, total_size):
    global start_time
    global last_update

    current_milli_time = lambda: int(time.time() * 1000)

    if count == 0:
        start_time = time.time()
        last_update = current_milli_time()
        return
    duration = time.time() - start_time
    progress_size = int(count * block_size)
    try:
        speed = int(progress_size / (1024 * duration))
    except ZeroDivisionError:
        speed = 0

    percent = int(count * block_size * 100 / total_size)
    if percent == 100 or (current_milli_time() - last_update) > 500:
        sys.stdout.write(
            "\r%d%%, %d MB, %d KB/s, %d seconds passed" % (percent, progress_size / (1024 * 1024), speed, duration)
        )
        sys.stdout.flush()
        last_update = current_milli_time()


def download(url, targetfile, show_progress=False, credentials=None):
    with requests.get(url, stream=True, auth=credentials) as r:
        with open(targetfile, "wb") as f:
            total_size = int(r.headers["Content-length"])
            progress = 0
            chunk_size = 32 * 1024
            if r.status_code == 200:
                for chunk in r.raw.stream(chunk_size, decode_content=False):
                    f.write(chunk)
                    if show_progress:
                        _report_hook(progress, chunk_size, total_size)
                        progress = progress + 1
    if show_progress:
        print("\n")
