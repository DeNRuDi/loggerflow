from collections import defaultdict
from datetime import timedelta
from statistics import mean

def aggregate_metrics(metrics, interval_seconds, interval_minutes) -> list:
    aggregated_data = defaultdict(lambda: {"cpu": [], "process_memory": [], "used_memory": [], "availability": []})
    for metric in metrics:
        if interval_minutes == 0:
            bucket_time = metric.last_heartbeat - timedelta(
                seconds=metric.last_heartbeat.second % interval_seconds,
                microseconds=metric.last_heartbeat.microsecond,
            )
        else:
            bucket_time = metric.last_heartbeat - timedelta(
                minutes=metric.last_heartbeat.minute % interval_minutes,
                seconds=metric.last_heartbeat.second,
                microseconds=metric.last_heartbeat.microsecond,
            )
        aggregated_data[bucket_time]["cpu"].append(metric.data["cpu"])
        aggregated_data[bucket_time]["process_memory"].append(metric.data["process_memory"])
        aggregated_data[bucket_time]["used_memory"].append(metric.data["used_memory"])
        # aggregated_data[bucket_time]["availability"].append(metric.data["availability"])

    grouped_metrics = []
    for timestamp, values in aggregated_data.items():
        grouped_metrics.append({
            "timestamp": timestamp,
            "cpu": mean(values["cpu"]),
            "process_memory": mean(values["process_memory"]),
            "used_memory": mean(values["used_memory"]),
            # "availability": max(values["availability"]),
        })
    return grouped_metrics


def get_aggregation_interval(filter_time: int) -> int:
    if filter_time <= 1:
        return 1
    elif filter_time <= 5:
        return 10
    elif filter_time <= 30:
        return 60
    elif filter_time <= 60:
        return 300
    elif filter_time <= 180:
        return 600
    elif filter_time <= 1440:
        return 1800
    elif filter_time <= 4320:
        return 3600
    else:
        return 14400
