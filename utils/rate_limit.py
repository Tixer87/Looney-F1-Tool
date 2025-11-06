import time

last_call_time = 0
MIN_INTERVAL = 0.25  # 4 Anfragen pro Sekunde

def enforce_rate_limit(func):
    def wrapper(*args, **kwargs):
        global last_call_time
        elapsed = time.time() - last_call_time
        if elapsed < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - elapsed)
        result = func(*args, **kwargs)
        last_call_time = time.time()
        return result
    return wrapper