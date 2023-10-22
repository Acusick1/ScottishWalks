import json
import pandas as pd
import re
from OSGridConverter import grid2latlong
from OSGridConverter.base import OSGridError
from config import settings


def capitalize_string(string: str, exceptions: list[str] = ['and', 'or', 'the', 'on', 'in', 'of', 'to', 'via', 'near', 'by', 'up', 'from']) -> str:
    # This regular expression captures words and their trailing punctuation
    pattern = r"([\w-]+['\w-]*[\.,!?:;]*)(\s*)"
    
    capitalized_words = []
    
    # Use findall to get a list of tuples where each tuple contains (word, space)
    for word, space in re.findall(pattern, string):
        
        # Capitalize the first word regardless of its presence in the exceptions list
        if not capitalized_words:
            capitalized_words.append(word.capitalize())
        elif word.lower() in exceptions:
            capitalized_words.append(word.lower())
        else:
            capitalized_words.append(word.capitalize())
            
        # Append the space or delimiter that followed the word
        capitalized_words.append(space)
        
    return ''.join(capitalized_words)


def format_operations(element):
    if isinstance(element, str) and not element.startswith("<"):
        # capitalize the string
        return capitalize_string(element)
    elif isinstance(element, (float, int)):
        # round the float to two decimal places
        return round(element, 2)
    else:
        return element
    

def html_link(link: str, text="click here") -> str:
    return f'<a href="{link}" target="blank">{text}</a>'


def series_to_html(row: pd.Series) -> str:
    return "".join(["<b>" + c + "</b>" + ": " + str(row[c]) + "<br>" for c in row.index])


def main():
    file_gen = settings.raw_data_path.glob("*walks.json")

    dfs = []  # an empty list to store the data frames
    for file in file_gen:
        with open(file) as f:
            data = json.load(f)
            dfs.append(pd.DataFrame(data))

    df = pd.concat(dfs, ignore_index=True)  # concatenate all the data frames in the list.

    # Data cleaning
    df = df.rename(columns={"Area0": "Region", "Area1": "Subregion", "StartPoint": "Start Point"})

    for col in df.columns:
        # Combining plural columns
        if col + 's' in df.columns:
            df[col] = df[col].fillna(df[col + 's'])
            df = df.drop(columns=col + 's')

    hill_names = ["munro", "corbett", "donald", "fiona", "sub 2000"]

    for hill_name in hill_names:
        
        hill_cols = [col for col in df.columns if hill_name in col.lower()]
        df[hill_cols] = df[hill_cols].fillna("").astype(str)
        combined_hill_col = df[hill_cols].agg(lambda x: ', '.join(filter(None, x)), axis=1)
        
        df.drop(columns=hill_cols, inplace=True)
        df[hill_name.capitalize()] = combined_hill_col

    df["Munros Climbed"] = df["Munro"].str.count(",") + 1
    df.loc[df["Munro"] == "", "Munros Climbed"] = 0

    # Kilometers
    df["Distance"] = df["Distance"].str.extract(r"^([0-9\.]*)").astype(float)
    
    # Does not seem to be used anymore
    # df["Time"].fillna(df["Time (summer conditions)"], inplace=True)
    # df.drop(columns="Time (summer conditions)", inplace=True)

    time = df["Time"].str.split("-", expand=True)
    minute_cells = time.apply(lambda x: x.str.contains("min")).astype(bool)
    minute_cells[0] = minute_cells[0] | minute_cells[1]

    for c in time.columns:
        time[c] = time[c].str.extract(r"(\d+\.?\d*)").astype(float)

    time[minute_cells] = time[minute_cells] / 60
    time[1].fillna(time[0], inplace=True)
    df["Time"] = time.mean(axis=1)

    df["Start Grid Ref"] = df["Start Grid Ref"].str.replace(" ", "")
    df["Rating"] = df["Rating"].astype(float)
    df["Votes"] = df["Votes"].astype(int)
    df["Ascent"] = df["Ascent"].str.extract(r"(\d+\.?\d*)").astype(int)
    df["Link"] = df["Link"].apply(lambda x: html_link(x))
    df["Start Point"] = df["Start Point"].apply(lambda x: html_link(x))
    df["GPX"] = df["GPX"].apply(lambda x: html_link(x, text="download"))

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
    df = df.applymap(format_operations)
    df["Start Grid Ref"] = df["Start Grid Ref"].str.upper()
    df = df.dropna(subset=["lat", "lon"])
    df.reset_index(drop=True, inplace=True)

    # Creating df for marker tooltip
    popup_df = df[["Name", "Distance", "Time", "Ascent", "Rating", "Link", "Start Point", "GPX"]].copy()
    popup_df["Distance"] = popup_df["Distance"].apply(lambda x: f"{x}km")
    popup_df["Ascent"] = popup_df["Ascent"].apply(lambda x: f"{x}m")
    popup_df["Rating"] = popup_df["Rating"].apply(lambda x: f"{x:.2f}/5")
    popup_df["Time"] = popup_df["Time"].apply(lambda x: f"{x:.2f} hours (avg)")
    
    df["Popup"] = popup_df.apply(series_to_html, axis=1)

    df.to_parquet(settings.processed_path)
    df.to_csv(settings.processed_path.with_suffix(".csv"))

    return df


if __name__ == "__main__":

    main()
