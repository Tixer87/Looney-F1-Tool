def time_as_int(timestr):
    if not timestr or not isinstance(timestr, str) or timestr.strip() == "":
        return 0
    parts = timestr.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
        total_ms = (int(hours) * 3600 + int(minutes) * 60 + float(seconds)) * 1000
    elif len(parts) == 2:
        minutes, seconds = parts
        total_ms = (int(minutes) * 60 + float(seconds)) * 1000
    else:
        try:
            total_ms = float(parts[0]) * 1000
        except ValueError:
            return 0
    return int(total_ms)
