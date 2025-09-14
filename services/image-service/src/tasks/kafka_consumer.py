# src/tasks/kafka_consumer.py
import json
import os
import logging
from kafka import KafkaConsumer

logger = logging.getLogger(__name__)

class ImageKafkaConsumer:
    def __init__(self, topic: str, group_id: str = "image-service-validate"):
        self.topic = topic
        self.group_id = group_id
        broker = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        
        logger.info(f"Inicializando consumidor Kafka para tópico '{topic}' con broker '{broker}' y group_id '{group_id}'")
        
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=[broker],
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            group_id=group_id,
            enable_auto_commit=True,
            auto_offset_reset='latest'  # Solo procesar mensajes nuevos
        )
        
        logger.info(f"Consumidor Kafka inicializado correctamente")
    
    def listen(self, callback):
        """Escucha mensajes y ejecuta el callback para cada uno"""
        logger.info(f"Iniciando escucha de mensajes en tópico '{self.topic}'...")
        
        try:
            for message in self.consumer:
                try:
                    logger.info(f"Mensaje recibido: {message.value}")
                    callback(message.value)
                except Exception as e:
                    logger.error(f"Error procesando mensaje: {str(e)}")
        except KeyboardInterrupt:
            logger.info("Interrumpido por el usuario")
        except Exception as e:
            logger.error(f"Error en el consumidor: {str(e)}")
        finally:
            self.consumer.close()
            logger.info("Consumidor cerrado")

# Función simple para compatibilidad con el archivo anterior
def start_validate_upload_consumer():
    """Inicia el consumidor para validate_upload"""
    from tasks.validation_tasks import validate_upload_task
    
    def process_message(message):
        validate_upload_task(
            message.get("job_id"),
            message.get("staging_path"),
            message.get("original_filename"),
            message.get("user_id"),
            message.get("custom_filename"),
        )
    
    consumer = ImageKafkaConsumer("validate_upload")
    consumer.listen(process_message)