import os

def get_file_size_mb(path):
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    return round(total_size / (1024 * 1024), 2)

def get_storage_stats():
    stats = {
        "sensor_storage": get_file_size_mb("storage/sensors.db"),
        "video_storage": get_file_size_mb("storage/videos"),
        "other_storage": get_file_size_mb("storage/others") if os.path.exists("storage/others") else 0.0,
    }
    stats["total_storage"] = round(sum(stats.values()), 2)
    return stats
