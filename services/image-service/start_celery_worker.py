#!/usr/bin/env python3
"""
Script para iniciar el worker de Celery para procesamiento de tumores en background.
"""

import os
import sys
from dotenv import load_dotenv

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

load_dotenv()

def start_celery_worker():
    """Inicia el worker de Celery"""
    try:
        from tasks.tumor_analysis_tasks import celery_app
        
        print("🧠 BrainLens - Iniciando Worker de Celery")
        print("=" * 50)
        print("📋 Configuración:")
        print(f"   - Broker: {os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')}")
        print(f"   - Cola: tumor_analysis")
        print(f"   - Modelo: {os.getenv('MODEL_PATH', 'modelo_multiclase_final.keras')}")
        print()
        
        # Verificar que el modelo existe
        model_path = os.getenv("MODEL_PATH", "modelo_multiclase_final.keras")
        if not os.path.exists(model_path):
            print(f"⚠️  Advertencia: Modelo no encontrado en {model_path}")
            print("   El worker funcionará pero las predicciones fallarán")
            print()
        
        print("🚀 Iniciando worker...")
        print("   Presiona Ctrl+C para detener")
        print()
        
        # Iniciar worker
        celery_app.worker_main([
            'worker',
            '--loglevel=info',
            '--queues=tumor_analysis',
            '--hostname=worker1@%h'
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Worker detenido por el usuario")
    except Exception as e:
        print(f"❌ Error iniciando worker: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    start_celery_worker()
