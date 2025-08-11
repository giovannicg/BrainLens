import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de Celery
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Configuración de tareas
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'UTC'
enable_utc = True

# Configuración de workers
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 1000

# Configuración de tareas específicas
task_routes = {
    'tasks.tumor_analysis_tasks.analyze_tumor_task': {'queue': 'tumor_analysis'}
}

# Configuración de colas
task_default_queue = 'default'
task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'tumor_analysis': {
        'exchange': 'tumor_analysis',
        'routing_key': 'tumor_analysis',
    }
}
