import logging
from .kafka_consumer import ImageKafkaConsumer

logger = logging.getLogger(__name__)


def process_tumor_analysis(message):
    logger.info(f"Mensaje recibido en worker_tumor_analysis: {message}")
    # Aquí iría la lógica de análisis de tumores
    # Por ahora solo logueamos el mensaje
    logger.info("Procesando análisis de tumor...")


def main():
    logger.info("Iniciando worker de análisis de tumores...")
    consumer = ImageKafkaConsumer(topic='tumor_analysis', group_id='image-service-analyze')
    logger.info("Worker de tumor_analysis escuchando...")
    consumer.listen(process_tumor_analysis)


if __name__ == "__main__":
    main()