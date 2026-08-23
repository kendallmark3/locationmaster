from dataclasses import dataclass
import os
import boto3

@dataclass
class GeocodeResult:
    label: str
    longitude: float
    latitude: float
    place_id: str
    provider: str = "amazon-location"

class AwsLocationGeocoder:
    def __init__(self):
        self.client = boto3.client("geo-places", region_name=os.getenv("AWS_REGION", "us-east-1"))

    def geocode(self, query: str) -> list[GeocodeResult]:
        response = self.client.geocode(QueryText=query, MaxResults=5, IntendedUse="Storage")
        return self._parse_results(response, fallback_label=query)

    def search_nearby(self, query: str, longitude: float, latitude: float, max_results: int = 5, max_distance_km: float = 25) -> list[GeocodeResult]:
        # BiasPosition only nudges ranking — it does not restrict results to the area, and
        # a generic query (e.g. "public transit station") can return the AWS Location
        # index's globally-best-ranked match (a different country's main train station)
        # ahead of a genuinely nearby but less prominent result. Over-fetch candidates and
        # hard-filter by the Distance AWS returns per result, so a bad match can only ever
        # be dropped, never silently outrank a real nearby place.
        response = self.client.search_text(
            QueryText=query,
            BiasPosition=[longitude, latitude],
            MaxResults=max(max_results * 3, 15),
            IntendedUse="Storage",
        )
        return self._parse_results(response, fallback_label=query, max_distance_m=max_distance_km * 1000)[:max_results]

    def reverse_geocode(self, longitude: float, latitude: float) -> list[GeocodeResult]:
        response = self.client.reverse_geocode(QueryPosition=[longitude, latitude], MaxResults=1, IntendedUse="Storage")
        return self._parse_results(response, fallback_label=f"{latitude}, {longitude}")

    def _parse_results(self, response: dict, fallback_label: str, max_distance_m: float | None = None) -> list[GeocodeResult]:
        items = response.get("ResultItems", [])
        if max_distance_m is not None:
            items = [i for i in items if i.get("Distance") is None or i.get("Distance") <= max_distance_m]
            items = sorted(items, key=lambda i: i.get("Distance") if i.get("Distance") is not None else float("inf"))
        results = []
        for item in items:
            pos = item.get("Position", [])
            if len(pos) != 2:
                continue
            results.append(GeocodeResult(
                label=item.get("Title") or fallback_label,
                longitude=pos[0],
                latitude=pos[1],
                place_id=item.get("PlaceId", ""),
            ))
        return results
