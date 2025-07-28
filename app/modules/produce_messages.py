from confluent_kafka import Producer  ##,AdminClient,KafkaException, NewPartitions
from utils.constants import BOOTSTRAP_SERVER
from utils.logger import FileLogs
import os

logs = FileLogs().get_logger(os.path.basename(__file__))

def kafka_producer_config():
    conf = {
        'bootstrap.servers': BOOTSTRAP_SERVER,  # Kafka broker
    }
    logs.info(f"connected to BOOTSTRAP_SERVER :- {BOOTSTRAP_SERVER} for Producer ")
    return Producer(**conf)

def produce_message(topic, key, message):
   
    producer = kafka_producer_config()
    producer.produce(topic=topic, key=key, value=message)
    producer.flush()  # Ensures the message is sent