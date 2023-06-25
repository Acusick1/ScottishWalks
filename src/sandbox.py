import json
import pandas as pd
from OSGridConverter import grid2latlong
from OSGridConverter.base import OSGridError
from src.settings import DATASET_PATH


def format_operations(element):
    if isinstance(element, str):
        # capitalize the first letter of the string
        return element.capitalize()
    elif isinstance(element, (float, int)):
        # round the float to two decimal places
        return round(element, 2)
    else:
        return element
    

def html_link(x, text="click here"):
    return f'<a href="{x}" target="blank">{text}</a>'


def main():
    file_gen = DATASET_PATH.glob("*walks.json")

    dfs = []  # an empty list to store the data frames
    for file in file_gen:
        with open(file) as f:
            data = json.load(f)
            dfs.append(pd.DataFrame(data))

    df = pd.concat(dfs, ignore_index=True)  # concatenate all the data frames in the list.

    # Data cleaning
    for col in df.columns:
        # Combining plural columns
        if col + 's' in df.columns:
            df[col] = df[col].fillna(df[col + 's'])
            df = df.drop(columns=col + 's')

    hill_names = ["corbett", "donald", "graham"]
    hill_columns = [col for col in df.columns if any(hill in col.lower() for hill in hill_names)]

    df[["Munro", "Sub 2000"]] = df[["Munro", "Sub 2000"]].fillna("")
    df["Munros Climbed"] = df["Munro"].str.count(",") + 1
    df.loc[df["Munro"] == "", "Munros Climbed"] = 0

    df[hill_columns] = df[hill_columns].fillna("").astype(str)
    # df[hill_columns] = df[hill_columns].astype(str)
    df["CGD"] = df[hill_columns].agg(lambda x: ', '.join(filter(None, x)), axis=1)
    df.drop(columns=hill_columns, inplace=True)

    # Kilometers
    df["Distance"] = df["Distance"].str.extract(r"^([0-9\.]*)")
    df["Time"].fillna(df["Time (summer conditions)"], inplace=True)
    df.drop(columns="Time (summer conditions)", inplace=True)

    test = df["Time"].str.split("-", expand=True)
    minute_cells = test.apply(lambda x: x.str.contains("min")).astype(bool)
    minute_cells[0] = minute_cells[0] | minute_cells[1]

    for c in test.columns:
        test[c] = test[c].str.extract(r"(\d+\.?\d*)").astype(float)

    test[minute_cells] = test[minute_cells] / 60
    test[1].fillna(test[0], inplace=True)
    df["Time"] = test.mean(axis=1)

    df["Rating"] = df["Rating"].astype(float)
    df["Votes"] = df["Votes"].astype(int)
    df["Ascent"] = df["Ascent"].str.extract(r"(\d+\.?\d*)").astype(int)
    df["Link"] = df["Link"].apply(lambda x: html_link(x))
    df["GPX"] = df["GPX"].apply(lambda x: html_link(x, text="dowlonad"))

    coords = {"lat": [], "lon": []}
    for p in df["Start Grid Ref"]:
        try:
            # TODO: This gives wrong longitude for some walks (e.g. castle stalker) but GPX gives correct position, may
            #   need to use starting point of that instead
            loc = grid2latlong(p)
            long = loc.longitude if loc.longitude > 0 else 360 + loc.longitude
            coords["lat"].append(float(loc.latitude))
            coords["lon"].append(float(long))
        except OSGridError:
            coords["lat"].append(None)
            coords["lon"].append(None)

    coords = pd.DataFrame(coords)
    df = pd.concat([df, coords], axis=1)
    df.drop(columns="Start Grid Ref", inplace=True)
    df.dropna(subset=["lat", "lon"], inplace=True)
    df = df.applymap(format_operations)

    df.reset_index(drop=True, inplace=True)

    return df


if __name__ == "__main__":

    main()
