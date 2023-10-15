import json
import pandas as pd
from config import settings


def load_walk_data() -> pd.DataFrame:
    file_gen = settings.raw_data_path.glob("*walks.json")

    dfs = []  # an empty list to store the data frames
    for file in file_gen:
        with open(file) as f:
            data = json.load(f)
            dfs.append(pd.DataFrame(data))

    return pd.concat(dfs, ignore_index=True)


if __name__ == "__main__":

    pass
