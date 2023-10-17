import pathlib
from dataclasses import dataclass

@dataclass
class Settings:

    root_path = pathlib.Path(__file__).parent
    data_path = root_path / "data"
    processed_path = data_path / "processed.parquet"
    processed_gpx_path = data_path / "processed_gpx.parquet"
    raw_data_path = data_path / "raw"
    request_delay = 0.5


settings = Settings()
