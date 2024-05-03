from fastapi import FastAPI
from typing import Union, List
from app.utils import RoutePoint, get_values_for_route

app = FastAPI()


@app.get("/")
def alive() -> dict:
    """Endpoint to check if the application is alive."""
    return {"status": "alive"}


@app.post("/dwd/{var}")
def get_forecast_values_for_locations(var: str, points: Union[RoutePoint, List[RoutePoint]]) -> List[float]:
    """Retrieve forecast values for a variable at specified locations along a route.

    Args:
        var (str): The variable to retrieve values for.
        points (Union[RoutePoint, List[RoutePoint]]): Either a single RoutePoint or a list of RoutePoint objects
        representing the route.
        Each RoutePoint should be a JSON object with the following keys:
        - lat: float
        - lon: float
        - time: str (ISO 8601 format)

    Returns:
        List[float]: List of forecast values corresponding to each point on the route.
    """
    if isinstance(points, RoutePoint):
        points = [points]
    return get_values_for_route(var, points)
