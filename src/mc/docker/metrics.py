import requests
from prometheus_client.parser import text_string_to_metric_families

METRICS_URL = "http://127.0.0.1:9323/metrics"

def get_docker_metrics(metrics_url):
    resp = requests.get(metrics_url, timeout=5)
    resp.raise_for_status()
    #return resp.text
    return text_string_to_metric_families(resp.text)


if __name__ == "__main__":
    #print(get_docker_metrics(METRICS_URL))

    for family in get_docker_metrics(METRICS_URL):
        if not family.name.startswith("engine_daemon"):
            continue
        for sample in family.samples:
            print(sample.name, sample.labels, sample.value)