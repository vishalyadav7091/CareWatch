import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load backend/.env
backend_dir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(backend_dir, ".env"))

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "carewatch_db")

# Safely encode credentials for MySQL URI
encoded_password = quote_plus(DB_PASSWORD)

# If cloud provider provides DATABASE_URL / MYSQL_URL, use it directly
raw_db_url = os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL")
if raw_db_url:
    if raw_db_url.startswith("mysql://"):
        raw_db_url = raw_db_url.replace("mysql://", "mysql+pymysql://", 1)
    database_uri = raw_db_url
elif os.getenv("RENDER") or (os.getenv("FLASK_ENV") == "production" and DB_HOST in ["127.0.0.1", "localhost"] and not DB_PASSWORD):
    # Standalone cloud container fallback (SQLite) when external MySQL is not configured
    database_uri = "sqlite:///carewatch.db"
else:
    database_uri = (
        f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )


# Test database URI: isolates all tests to carewatch_test_db so development DB is NEVER touched
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "carewatch_test_db")
test_database_uri = (
    f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}?charset=utf8mb4"
)


class Config:
    """Base configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "carewatch-default-secret-key")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"
    PORT = int(os.getenv("PORT", 5000))
    HOST = os.getenv("HOST", "127.0.0.1")

    # Security & CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours in seconds

    # SQLAlchemy Configuration

    SQLALCHEMY_DATABASE_URI = database_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    }


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False


class TestingConfig(Config):
    """Testing configuration. Uses isolated test database carewatch_test_db."""

    TESTING = True
    DEBUG = False
    # Uses isolated test database carewatch_test_db so development DB is NEVER touched
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URI", test_database_uri)
    JWT_SECRET_KEY = "carewatch-testing-jwt-secret-key"
    WTF_CSRF_ENABLED = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
