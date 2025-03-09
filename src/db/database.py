from src.config import settings

TORTOISE_ORM = {
    "connections": {
        "default": "sqlite://db.sqlite3"  # You can change this to your actual DB connection
    },
    "apps": {
        "models": {
            "models": ["src.db.models", "aerich.models"],
            "default_connection": "default",
        }
    }
}