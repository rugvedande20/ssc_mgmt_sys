from pathlib import Path

from pydantic import BaseModel
from sqlalchemy import URL


class AppSettings(BaseModel):
    app_name: str = "Student Success and Career Navigation Management System"
    app_version: str = "0.1.0"
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    demo_dir: Path = data_dir / "demo"
    cache_dir: Path = data_dir / "cache"
    db_path: Path = data_dir / "app.db"
    model_dir: Path = base_dir / "models"
    secret_key: str = "replace-me-in-production"

    @property
    def database_url(self) -> str:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return str(URL.create("sqlite", database=str(self.db_path.resolve())))


settings = AppSettings()
