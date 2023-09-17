import pathlib
from dataclasses import dataclass

@dataclass
class Settings:

    root_path = pathlib.Path(__file__).parent
    processed_path = root_path / "data" / "processed.parquet"
    raw_data_path = root_path / "data" / "raw"


settings = Settings()
