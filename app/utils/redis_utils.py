import redis
from utils.constants import REDIS_HOST , REDIS_PORT
import pickle

redis_conn = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=3)
redis_conn = redis.Redis(connection_pool=redis_conn)

def update_redis_summary(summary,key):
    summary = pickle.dumps(summary)
    return redis_conn.set(key, summary)

def get_redis_summary(key):
    if redis_conn.exists(key):
        summary = redis_conn.get(key)
        summary_data = pickle.loads(summary)
        return summary_data
    else:
        return None