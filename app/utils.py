from dwdGribExtractor.icon import ICON_EU
from datetime import datetime, timezone
import numpy as np
from pydantic import BaseModel
from typing import List
import os

# Set up cache directory for grib files
__ICON_CACHE_DIR = os.environ.get("ICON_CACHE_DIR", "/tmp/icon_cache")
if not os.path.exists(__ICON_CACHE_DIR):
    os.makedirs(__ICON_CACHE_DIR)


class RoutePoint(BaseModel):
    """Model representing a point along a route with latitude, longitude, and time."""
    lat: float
    lon: float
    time: str


def next_run(run_number: str = "00") -> str:
    """Calculate the next run number based on the provided run number.

    Args:
        run_number (str): The current run number in "HH" format. Defaults to "00".

    Returns:
        str: The next run number in "HH" format.
    """
    return str(0 if run_number == "21" else int(run_number) + 3).zfill(2)


def get_values_for_route(variable: str, route: List[RoutePoint]) -> List:
    """Retrieve forecast values for a given variable along a route.

    Args:
        variable (str): The variable to retrieve values for.
        route (List[RoutePoint]): List of RoutePoint objects representing the route.

    Returns:
        List: List of forecast values corresponding to each point on the route.
    """
    # Determine current time and forecast hours
    now = datetime.now().astimezone()
    times = [datetime.fromisoformat(point.time).astimezone() for point in route]
    forecast_hours = int(np.ceil(abs(max(times) - now).total_seconds() / 3600))

    # Create location list for forecast
    location_list = {i: {"lat": point.lat, "lon": point.lon} for i, point in enumerate(route)}

    # Retrieve forecast data
    forecast = ICON_EU(
        locations=location_list,
        forecastHours=forecast_hours,
        tmpFp=__ICON_CACHE_DIR,
    )
    data = forecast.collectData(varList=[variable], cores=None)

    # Extract forecast values for each point on the route
    values = [
        data[variable][str(i), now.strftime("%Y-%m-%d")][times[i].astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")]
        for i in range(len(route))
    ]
    return values


if __name__ == "__main__":
    print("the current time in utc is:", datetime.now(timezone.utc))

    # Define a sample route
    route = [
        RoutePoint(lat=48.20, lon=16.37, time="2024-05-02T22:00:00"),
        RoutePoint(lat=47.07, lon=15.43, time="2024-05-02T23:00:00"),
    ]

    # Retrieve and print forecast values for the route
    print(get_values_for_route("t_2m", route))
