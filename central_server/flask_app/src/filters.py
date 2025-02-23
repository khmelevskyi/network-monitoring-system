from datetime import datetime


# Defining of the time_ago filter
def time_ago_filter(last_seen):
    if last_seen:
        delta = datetime.now() - last_seen
        return f"{int(delta.total_seconds() // 60)} minutes ago"
    else:
        return "Never"

