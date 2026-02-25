import time
import requests
from typing import Iterable

from graph_creation.domain.graph_creator import Flight
from graph_creation.application.ports import FlightProvider

class OpenSkyOAuthClient:
    """
    Handles OAuth2 client_credentials token acquisition + caching.
    """

    TOKEN_URL = (
        "https://auth.opensky-network.org/"
        "auth/realms/opensky-network/protocol/openid-connect/token"
    )

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token: str | None = None
        self._expires_at: float = 0

    def get_token(self) -> str:
        # Reuse token if still valid (with 30s safety margin)
        if self._access_token and time.time() < self._expires_at - 30:
            return self._access_token

        resp = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=30,
        )
        resp.raise_for_status()

        payload = resp.json()
        self._access_token = payload["access_token"]

        # expires_in is usually provided
        expires_in = payload.get("expires_in", 300)
        self._expires_at = time.time() + expires_in

        return self._access_token


class OpenSkyFlightProvider(FlightProvider):
    """
    FlightProvider implementation using OAuth2.
    Responsible only for:
    - calling API
    - filtering invalid flights
    - mapping to Domain Flight objects
    """

    BASE_URL = "https://opensky-network.org/api/flights/all"

    def __init__(self, client_id: str, client_secret: str):
        self._oauth = OpenSkyOAuthClient(client_id, client_secret)

    def load_flights(self, begin: int, end: int) -> Iterable[Flight]:
        token = self._oauth.get_token()

        resp = requests.get(
            self.BASE_URL,
            params={"begin": begin, "end": end},
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        resp.raise_for_status()

        data = resp.json()

        print(f"loaded {len(data)} flights from OpenSky")
        unknown_flights_number = 0

        for f in data:
            if not self._is_valid_flight(f):
                unknown_flights_number += 1
                continue

            yield Flight(
                flight_icao=f["icao24"],
                dep_icao=f["estDepartureAirport"],
                arr_icao=f["estArrivalAirport"],
            )
        
        print(f"flights with empty arr/dep = {unknown_flights_number}")

    @staticmethod
    def _is_valid_flight(f: dict) -> bool:
        return (f.get("estDepartureAirport") is not None 
                and f.get("estArrivalAirport") is not None
        )