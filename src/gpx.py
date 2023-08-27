import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from src import data


def parse(link: str):

    response = requests.get(link)
    soup = BeautifulSoup(response.text, "xml")
    coords = soup.find_all("rtept")

    info = []
    for c in coords:

        attrs = c.attrs
        attrs["ele"] = c.find("ele").contents[0]
        info.append(attrs)

    return pd.DataFrame(info).astype(float)


def get_lat_long_tuples(df: pd.DataFrame) -> list[tuple[float, float]]:

    return list(zip(df.lat, df.lon))


def positive_long(df: pd.DataFrame, col="lon") -> pd.DataFrame:

    df[col] = np.where(df[col] < 0, 360 + df[col], df[col])
    return df


if __name__ == "__main__":

    walk_data = data.load_walk_data()

    for gpx_link in walk_data["GPX"]:
        test = parse(gpx_link)
        test = positive_long(test)
