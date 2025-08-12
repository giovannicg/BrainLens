#!/usr/bin/env python3
"""
Script para configurar la integración con Google Colab
"""

import os
import json
import requests
from datetime import datetime

def setup_colab_integration():
    """Configurar la integración con Colab"""
    
    print("🚀 CONFIGURACIÓN DE INTEGRACIÓN CON COLAB")
    print("=" * 50)
    
    # Configuración del servicio Colab
    colab_config = {
        "notebook_url": input("📝 URL del notebook de Colab: ").strip(),
        "google_drive_folder_id": input("📁 ID de la carpeta de Google Drive (opcional): ").strip() or None,
        "api_key": input("🔑 API Key (opcional): ").strip() or None
    }
    
    # Configurar el servicio
    print("\n🔧 Configurando servicio de Colab...")
    
    try:
        response = requests.post(
            "http://localhost:8004/configure",
            json=colab_config,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Servicio de Colab configurado exitosamente")
        else:
            print(f"❌ Error configurando servicio: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al servicio de Colab")
        print("   Asegúrate de que el servicio esté ejecutándose en el puerto 8004")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Crear archivo de configuración
    config_file = "colab_config.json"
    with open(config_file, 'w') as f:
        json.dump({
            "colab_config": colab_config,
            "timestamp": datetime.utcnow().isoformat(),
            "instructions": {
                "notebook_setup": [
                    "1. Abre el notebook de Colab",
                    "2. Ejecuta todas las celdas en orden",
                    "3. Sube tu modelo a Google Drive",
                    "4. El servidor API estará disponible en el puerto 8080"
                ],
                "integration_methods": [
                    "Opción 1: Google Drive - Sube imágenes a Drive y el notebook las procesa",
                    "Opción 2: API Directa - Envía imágenes directamente al notebook"
                ]
            }
        }, f, indent=2)
    
    print(f"\n💾 Configuración guardada en: {config_file}")
    
    # Mostrar instrucciones
    print("\n📋 INSTRUCCIONES:")
    print("1. Abre el notebook de Colab proporcionado")
    print("2. Ejecuta todas las celdas en orden")
    print("3. Sube tu modelo 'modelo_multiclase_final.keras' a Google Drive")
    print("4. El notebook estará listo para procesar imágenes")
    print("5. Tu aplicación Docker puede enviar imágenes al servicio de Colab")
    
    return colab_config

def test_colab_connection():
    """Probar la conexión con el servicio de Colab"""
    
    print("\n🧪 PROBANDO CONEXIÓN CON COLAB")
    print("=" * 30)
    
    try:
        # Probar health check
        response = requests.get("http://localhost:8004/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Servicio de Colab está funcionando")
            
            # Probar status
            status_response = requests.get("http://localhost:8004/status", timeout=5)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"📊 Estado: {status_data['status']}")
                print(f"🔧 Colab configurado: {status_data['colab_configured']}")
            else:
                print("⚠️ No se pudo obtener el estado del servicio")
                
        else:
            print(f"❌ Servicio no responde correctamente: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al servicio de Colab")
        print("   Ejecuta: docker-compose up colab-service")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    
    print("🧠 BrainLens - Configuración de Integración con Colab")
    print("=" * 60)
    
    # Verificar si el servicio está ejecutándose
    test_colab_connection()
    
    # Configurar integración
    config = setup_colab_integration()
    
    # Probar conexión nuevamente
    test_colab_connection()
    
    print("\n🎉 CONFIGURACIÓN COMPLETADA")
    print("=" * 30)
    print("Tu aplicación ahora puede usar Google Colab para procesar imágenes.")
    print("El servicio de Colab está disponible en: http://localhost:8004")

if __name__ == "__main__":
    main() 