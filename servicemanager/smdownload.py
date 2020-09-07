import requests
import time
import sys


def _current_milli_time():
    return int(time.time() * 1000)


def _report_hook(count, block_size, total_size, start_time, last_update):
    duration = (_current_milli_time() - start_time) / 1000
    progress_size = int(count * block_size)
    try:
        speed = int(progress_size / duration / 1024)
    except ZeroDivisionError:
        speed = 0

    percent = int(count * block_size * 100 / total_size)
    if percent == 100 or (_current_milli_time() - last_update) > 500:
        sys.stdout.write(
            "\r%d%%, %d MB, %d KB/s, %d seconds passed" % (percent, progress_size / (1024 * 1024), speed, duration)
        )
        sys.stdout.flush()
        last_update = _current_milli_time()

    return start_time, last_update


def download(url, targetfile, show_progress=False, credentials=None):
    start_time = _current_milli_time()
    last_update = start_time
    with requests.get(url, stream=True, auth=credentials) as r:
        with open(targetfile, "wb") as f:
            total_size = int(r.headers["Content-length"])
            progress = 0
            chunk_size = 32 * 1024
            if r.status_code == 200:
                for chunk in r.raw.stream(chunk_size, decode_content=False):
                    f.write(chunk)
                    if show_progress:
                        start_time, last_update = _report_hook(progress, chunk_size, total_size, start_time, last_update)
                        progress = progress + 1
    if show_progress:
        print("\n")


def header(url, header_name):
    value = None
    with requests.head(url) as r:
        value = r.headers.get(header_name)
    return value
