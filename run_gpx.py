import re
import pandas as pd
from time import sleep
from src.gpx import parse, positive_long
from config import settings

url_pattern = re.compile(r'href=[\'"]?([^\'" >]+)')


def process_row(row: pd.Series):

    try:

        match = url_pattern.search(row["GPX"])
        url = match.group(1)
        print(f"Fetching: {url}")

        gpx_path = parse(url)
        gpx_path = positive_long(gpx_path)
        return {
            "index": row.name,
            "path": list(zip(gpx_path["lat"].to_list(), gpx_path["lon"].to_list()))
        }
    except Exception as e:
        print(e)


def full():

    walk_data = pd.read_parquet(settings.processed_path)

    all_paths = []
    # Make requests slowly
    for _, row in walk_data.iterrows():

        data = process_row(row)
        
        if data is not None:
            all_paths.append(data)
        
        sleep(settings.request_delay)
        
    paths_df = pd.DataFrame(all_paths).set_index("index")
    gpx_walk_data = walk_data.join(paths_df)

    gpx_walk_data.to_parquet(settings.processed_gpx_path, engine="fastparquet")
    gpx_walk_data.to_csv(settings.processed_gpx_path.with_suffix(".csv"))


def update():

    gpx_walk_data = pd.read_parquet(settings.processed_gpx_path)

    for index, row in gpx_walk_data.iterrows():

        if row["path"] is None:
            data = process_row(row)
            gpx_walk_data.at[index, "path"] = data["path"]
            sleep(settings.request_delay)

    gpx_walk_data.to_parquet(settings.processed_gpx_path, engine="fastparquet")
    gpx_walk_data.to_csv(settings.processed_gpx_path.with_suffix(".csv"))


def migrate():

    data = pd.read_parquet(settings.processed_gpx_path)
    data["path"] = data["path"].apply(lambda x: [list(y) for y in x])
    data.to_parquet(settings.processed_gpx_path, engine="fastparquet")
    data.to_csv(settings.processed_gpx_path.with_suffix(".csv"))


if __name__ == "__main__":
    
    full()
    update()
    # migrate()
    
