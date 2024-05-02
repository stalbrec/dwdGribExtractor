from dwdGribExtractor.icon import ICON_EU
import datetime


if __name__ == "__main__":
    locationList = {"Vienna": {"lat": 48.20, "lon": 16.37}, "Graz": {"lat": 47.07, "lon": 15.43}}

    variables = ["t_2m"]
    print("the current time in utc is:", datetime.datetime.now(datetime.timezone.utc))

    forecast = ICON_EU(locations=locationList, forecastHours=3)
    data = forecast.collectData(varList=variables, cores=None)
    loc = "Graz"
    result = (
        data["t_2m"][loc][datetime.datetime.now().strftime("%Y-%m-%d")][
            (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)).strftime("%Y-%m-%d %H:00")
        ]
        - 273.15
    )
    print(f"the temperature in {loc} in 3 hour is: {result:.2f} °C")
