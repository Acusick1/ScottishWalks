import pathlib
from dataclasses import dataclass

@dataclass
class Settings:

    root_path = pathlib.Path(__file__).parent
    data_path = root_path / "data"
    processed_path = data_path / "processed.parquet"
    display_path = data_path / "display.parquet"
    raw_data_path = data_path / "raw"


settings = Settings()
