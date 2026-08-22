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
        results = []
        for item in response.get("ResultItems", []):
            pos = item.get("Position", [])
            if len(pos) != 2:
                continue
            results.append(GeocodeResult(
                label=item.get("Title") or query,
                longitude=pos[0],
                latitude=pos[1],
                place_id=item.get("PlaceId", ""),
            ))
        return results
