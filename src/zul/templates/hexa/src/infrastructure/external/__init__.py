"""
Client untuk layanan pihak ketiga: payment gateway, email, API partner.

Gunanya:
    Membungkus API luar dalam class kecil supaya bagian lain aplikasi tidak
    bergantung pada bentuk respons vendor.

Contoh:
    # infrastructure/external/weather_api.py
    class WeatherApi:
        def __init__(self, api_key: str) -> None:
            self._client = httpx.Client(base_url="https://api.example.com")
            self._api_key = api_key

        def current(self, location: str) -> str:
            params = {"q": location, "key": self._api_key}
            response = self._client.get("/weather", params=params)
            response.raise_for_status()

            return response.json()["summary"]
"""
