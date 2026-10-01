def time_as_int(timestr):
    if not isinstance(timestr,str) or not timestr.strip():return 0
    parts=timestr.split(":")
    try:
        if len(parts)==3:
            hours,minutes,seconds=parts
            return int((int(hours)*3600+int(minutes)*60+float(seconds))*1000)
        if len(parts)==2:
            minutes,seconds=parts
            return int((int(minutes)*60+float(seconds))*1000)
        return int(float(parts[0])*1000)
    except ValueError:
        return 0