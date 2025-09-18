import json
import os
import logging
from kafka import KafkaProducer

logger = logging.getLogger(__name__)

class ImageKafkaProducer:
    def __init__(self, kafka_server=None):
        if kafka_server is None:
            kafka_server = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        
        logger.info(f"Inicializando producer Kafka con servidor: {kafka_server}")
        
        self.producer = KafkaProducer(
            bootstrap_servers=[kafka_server],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def send(self, topic, message):
        logger.info(f"Enviando mensaje a tópico '{topic}': {message}")
        future = self.producer.send(topic, message)
        self.producer.flush()
        logger.info(f"Mensaje enviado exitosamente a '{topic}'")