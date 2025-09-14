import logging
from .kafka_consumer import ImageKafkaConsumer

logger = logging.getLogger(__name__)


def process_image_chat(message):
    logger.info(f"Mensaje recibido en worker_image_chat: {message}")
    # Aquí iría la lógica de chat de imágenes
    # Por ahora solo logueamos el mensaje
    logger.info("Procesando chat de imagen...")


def main():
    logger.info("Iniciando worker de chat de imágenes...")
    consumer = ImageKafkaConsumer(topic='image_chat', group_id='image-service-chat')
    logger.info("Worker de image_chat escuchando...")
    consumer.listen(process_image_chat)


if __name__ == "__main__":
    main()