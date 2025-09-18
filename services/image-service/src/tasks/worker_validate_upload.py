import logging
from .kafka_consumer import ImageKafkaConsumer
from .validation_tasks import validate_upload_task

logger = logging.getLogger(__name__)


def process_validate_upload(message):
    logger.info(f"Mensaje recibido en worker_validate_upload: {message}")
    job_id = message.get('job_id')
    staging_path = message.get('staging_path')
    original_filename = message.get('original_filename')
    user_id = message.get('user_id')
    custom_filename = message.get('custom_filename')
    if job_id and staging_path and original_filename and user_id:
        logger.info(f"Ejecutando validate_upload_task con job_id={job_id}, staging_path={staging_path}, original_filename={original_filename}, user_id={user_id}, custom_filename={custom_filename}")
        try:
            validate_upload_task(job_id, staging_path, original_filename, user_id, custom_filename)
            logger.info(f"Tarea de validación médica ejecutada para job_id={job_id}")
        except Exception as e:
            logger.error(f"Error procesando validación/upload para job {job_id}: {str(e)}")
    else:
        logger.error(f"Mensaje de validate_upload incompleto: job_id={job_id}, staging_path={staging_path}, original_filename={original_filename}, user_id={user_id}")


def main():
    logger.info("Iniciando worker de validación de upload...")
    consumer = ImageKafkaConsumer(topic='validate_upload')
    logger.info("Worker de validate_upload escuchando...")
    consumer.listen(process_validate_upload)


if __name__ == "__main__":
    main()