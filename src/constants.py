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

SQS_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/765826404413/training-queue"
MODEL_BUCKET_NAME = "model-bucket-20240826061620914100000001"
REDIS_CACHE_PREFIX = "model_cache:"
