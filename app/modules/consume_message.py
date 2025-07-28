from confluent_kafka import Consumer,TopicPartition
from utils.constants import BOOTSTRAP_SERVER
import asyncio
import os
from utils.logger import FileLogs
from utils.utils_funcs import get_topic_key

logs = FileLogs().get_logger(os.path.basename(__file__))


class ConsumeMsg:

    def __init__(self):
        self.consumer = None

    def __del__(self):
        if self.consumer:
            logs.info("closing consumer ..")
            self.consumer.close()


    def kafka_consumer_config(self):
        conf = {
            'bootstrap.servers': BOOTSTRAP_SERVER,
            'group.id': 'ai_analysis',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False    
            }
        logs.info(f"connected to BOOTSTRAP_SERVER :- {BOOTSTRAP_SERVER} for CONSUMER")

        return Consumer(**conf)

    def consume_message(self, topic, user_id, product_id):
        key = get_topic_key(product_id, user_id)
        self.consumer = self.kafka_consumer_config()
        self.consumer.assign([TopicPartition(topic, 0 )])

        while True:
            msg = self.consumer.poll(2)
            if msg is not None:
                logs.info(f"msg_value :- {msg.value().decode('utf-8')},msg_key :- {msg.key().decode('utf-8')}")
            if msg is None:
                break
            if msg.error():
                break
            if msg.key() is not None and msg.key().decode('utf-8') == key:
                response = msg.value().decode('utf-8')
                yield response + "\n"


def consume_message(topic, user_id, product_id):
    kafka_con = ConsumeMsg()
    logs.info("kafka_connection..")
    generate_msg = kafka_con.consume_message(topic, user_id, product_id)
    for msg in generate_msg:
        yield msg
