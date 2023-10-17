import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup


def parse(link: str) -> pd.DataFrame:

    response = requests.get(link)
    soup = BeautifulSoup(response.text, "xml")
    coords = soup.find_all("rtept")

    info = [c.attrs for c in coords]

    return pd.DataFrame(info).astype(float)


def get_lat_long_tuples(df: pd.DataFrame) -> list[tuple[float, float]]:

    return list(zip(df.lat, df.lon))


def positive_long(df: pd.DataFrame, col="lon") -> pd.DataFrame:

    df[col] = np.where(df[col] < 0, 360 + df[col], df[col])
    return df
