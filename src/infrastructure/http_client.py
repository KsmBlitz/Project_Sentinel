import httpx


class HTTPClient:
    def get(self, url: str, timeout: int = 10) -> dict:
        try:
            response = httpx.get(url, timeout=timeout, follow_redirects=True)
            return {
                "is_up": response.status_code < 500,
                "status_code": response.status_code,
                "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                "error_msg": None,
            }
        except httpx.TimeoutException:
            return {"is_up": False, "status_code": None, "response_time_ms": None, "error_msg": "timeout"}
        except httpx.RequestError as e:
            return {"is_up": False, "status_code": None, "response_time_ms": None, "error_msg": str(e)}
