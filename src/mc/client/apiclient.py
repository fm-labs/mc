import requests

class McApiClient:

    def __init__(self, api_url: str, api_key: str = None):
        self.api_url = api_url
        self.api_key = api_key


    def _request(self, method: str, endpoint: str, **kwargs):
        url = self.api_url.rstrip("/") + "/api/" + endpoint.lstrip("/")
        print(f"Making {method.upper()} request to {url} with kwargs: {kwargs}")
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            del kwargs["headers"]
        kwargs["headers"] = headers
        try:
            res = requests.request(method, url, **kwargs)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"Error making request to {url}: {e}")
            raise

    def get(self, endpoint: str, **kwargs):
        return self._request("get", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs):
        return self._request("post", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs):
        return self._request("put", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs):
        return self._request("delete", endpoint, **kwargs)

    def get_info(self):
        return self.get("/info")
