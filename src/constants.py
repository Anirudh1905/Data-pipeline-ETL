STREAM_NAME = "app-stream"
REDIS_HOST = "my-redis-cluster.wahhz8.0001.use1.cache.amazonaws.com"
REDIS_PORT = 6379
DB_HOST = (
    "terraform-20240814061606792700000001.cknlstpybgat.us-east-1.rds.amazonaws.com"
)
DB_PORT = 5432
DB_NAME = "data_db"
DB_USER = "postgres"
DB_PASSWORD = "password"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
