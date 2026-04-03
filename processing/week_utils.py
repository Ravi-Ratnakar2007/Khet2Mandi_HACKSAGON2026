from datetime import datetime, timedelta

def week_to_dates(week):

    year, month, w = week.split("-")
    w = int(w.replace("W",""))

    start = datetime(int(year), int(month), 1) + timedelta(days=(w-1)*7)
    end = start + timedelta(days=6)

    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")