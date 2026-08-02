import httpx

from app.config import settings

_client = httpx.AsyncClient()


class OPAClient:
    def __init__(self):
        self.base_url = settings.opa_url

    async def evaluate(self, input_data: dict) -> dict:
        resp = await _client.post(
            f"{self.base_url}/v1/data/agent/spend",
            json={"input": input_data},
            timeout=5.0,
        )
        resp.raise_for_status()
        result = resp.json()
        return result.get("result", {})


opa_client = OPAClient()
