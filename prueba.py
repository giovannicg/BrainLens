"""
Script para probar los endpoints /predict y /predict-raw
"""

import os
import requests
import base64
import json
import time
from pathlib import Path

# Configuración
SERVER_BASE_URL = "https://379339addf89.ngrok-free.app"
DOWNLOADS_PATH = Path(r"C:\Users\willy\Desktop\Máster\TFM\BrainLens\BrainLens")  # Ruta a carpeta con imágenes

def get_image_files(directory):
    """Obtiene lista de archivos de imagen en el directorio"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    image_files = []
    
    if not directory.exists():
        print(f"❌ El directorio {directory} no existe")
        return image_files
    
    for file in directory.iterdir():
        if file.is_file() and file.suffix.lower() in image_extensions:
            image_files.append(file)
    
    return sorted(image_files)

def test_health_endpoint():
    """Prueba el endpoint /health"""
    try:
        print("🔍 Probando endpoint /health...")
        response = requests.get(f"{SERVER_BASE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Servidor OK: {response.json()}")
            return True
        else:
            print(f"❌ Servidor responde con error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando al servidor: {e}")
        return False

def test_predict_multipart(image_path):
    """Prueba el endpoint /predict con multipart/form-data"""
    print(f"\n📤 Probando /predict (multipart) con: {image_path.name}")
    print(f"   📁 Tamaño archivo: {image_path.stat().st_size / 1024:.1f} KB")
    
    try:
        with open(image_path, 'rb') as image_file:
            files = {'image': (image_path.name, image_file, 'image/jpeg')}
            
            print("   ⏳ Enviando petición...")
            start_time = time.time()
            response = requests.post(
                f"{SERVER_BASE_URL}/predict",
                files=files,
                timeout=30
            )
            request_time = time.time() - start_time
            
        print(f"   📡 Status Code: {response.status_code}")
        print(f"   ⏱️ Tiempo respuesta: {request_time:.2f}s")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ Respuesta JSON exitosa:")
                print(f"   📊 Status: {result.get('status')}")
                print(f"   📊 Predicción: {result.get('prediction')}")
                print(f"   📊 Confianza: {result.get('confidence', 0):.4f}")
                
                # Mostrar detalles si están disponibles
                if 'details' in result:
                    details = result['details']
                    if 'stage_1' in details:
                        stage1 = details['stage_1']
                        print(f"   🔬 Etapa 1 - Prob. tumor: {stage1.get('mean_tumor_probability', 0):.4f}")
                        print(f"   🔬 Etapa 1 - Hay tumor: {stage1.get('has_tumor', False)}")
                    
                    if 'stage_2' in details:
                        stage2 = details['stage_2']
                        print(f"   🔬 Etapa 2 - Mejor clase: {stage2.get('best_class')}")
                        print(f"   🔬 Etapa 2 - Confianza: {stage2.get('best_class_confidence', 0):.4f}")
                        if 'mean_class_probabilities' in stage2:
                            print("   📈 Probabilidades por clase:")
                            for clase, prob in stage2['mean_class_probabilities'].items():
                                print(f"      - {clase}: {prob:.4f}")
                
                return True
            except json.JSONDecodeError as e:
                print(f"❌ Error decodificando JSON: {e}")
                print(f"   📄 Respuesta raw: {response.text[:500]}...")
                return False
        else:
            print(f"❌ Error HTTP {response.status_code}")
            print(f"   📄 Headers: {dict(response.headers)}")
            try:
                error_data = response.json()
                print(f"   📄 Error JSON: {error_data}")
            except:
                print(f"   📄 Error texto: {response.text[:500]}...")
            return False
            
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout ({30}s): {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {type(e).__name__}: {e}")
        return False

def test_predict_raw_base64(image_path):
    """Prueba el endpoint /predict-raw con base64"""
    print(f"\n📤 Probando /predict-raw (base64) con: {image_path.name}")
    
    try:
        # Codificar imagen en base64
        with open(image_path, 'rb') as image_file:
            image_bytes = image_file.read()
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        payload = {"image_data": image_b64}
        
        start_time = time.time()
        response = requests.post(
            f"{SERVER_BASE_URL}/predict-raw",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Respuesta exitosa en {request_time:.2f}s:")
            print(f"   📊 Predicción: {result.get('prediction')}")
            print(f"   📊 Confianza: {result.get('confidence', 0):.4f}")
            
            # Mostrar detalles completos si están disponibles
            if 'full_details' in result:
                details = result['full_details']
                print(f"   ⏱️ Tiempo total servidor: {details.get('total_time', 0):.3f}s")
                
                # Detalles de etapa 1
                if 'stage_1' in details:
                    stage1 = details['stage_1']
                    print(f"   🔬 Etapa 1 detalles:")
                    print(f"      - Probabilidades individuales: {[f'{p:.3f}' for p in stage1.get('individual_tumor_probs', [])]}")
                    print(f"      - Media: {stage1.get('mean_tumor_probability', 0):.4f}")
                
                # Detalles de etapa 2
                if 'stage_2' in details:
                    stage2 = details['stage_2']
                    print(f"   🔬 Etapa 2 detalles:")
                    print(f"      - Probabilidades medias: {stage2.get('mean_class_probabilities', {})}")
                    if 'individual_class_probs' in stage2:
                        print("      - Probabilidades individuales por modelo:")
                        for clase, probs in stage2['individual_class_probs'].items():
                            if probs:
                                print(f"        * {clase}: {[f'{p:.3f}' for p in probs]}")
            
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba base64: {e}")
        return False

def test_predict_base64(image_path):
    """Prueba el endpoint /predict con base64 (fallback)"""
    print(f"\n📤 Probando /predict (base64 fallback) con: {image_path.name}")
    
    try:
        # Codificar imagen en base64
        with open(image_path, 'rb') as image_file:
            image_bytes = image_file.read()
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        payload = {"image_data": image_b64}
        
        start_time = time.time()
        response = requests.post(
            f"{SERVER_BASE_URL}/predict",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Respuesta exitosa en {request_time:.2f}s:")
            print(f"   📊 Predicción: {result.get('prediction')}")
            print(f"   📊 Confianza: {result.get('confidence', 0):.4f}")
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba base64: {e}")
        return False

def main():
    print("🧠 Script de prueba para API de predicción de tumores cerebrales")
    print(f"🌐 Servidor: {SERVER_BASE_URL}")
    print(f"📁 Carpeta de imágenes: {DOWNLOADS_PATH}")
    print("="*60)
    
    # 1. Verificar conectividad
    if not test_health_endpoint():
        print("\n❌ No se puede conectar al servidor. Verifica que esté ejecutándose.")
        return
    
    # 2. Buscar imágenes
    image_files = get_image_files(DOWNLOADS_PATH)
    if not image_files:
        print(f"\n❌ No se encontraron imágenes en {DOWNLOADS_PATH}")
        print("   Formatos soportados: .jpg, .jpeg, .png, .bmp, .tiff, .webp")
        return
    
    print(f"\n📷 Encontradas {len(image_files)} imágenes:")
    for i, img in enumerate(image_files[:5]):  # Mostrar solo las primeras 5
        print(f"   {i+1}. {img.name} ({img.stat().st_size / 1024:.1f} KB)")
    
    if len(image_files) > 5:
        print(f"   ... y {len(image_files) - 5} más")
    
    # 3. Seleccionar imagen para probar
    try:
        selection = input(f"\n🔢 Selecciona imagen (1-{len(image_files)}) o Enter para usar la primera: ").strip()
        if selection == "":
            selected_idx = 0
        else:
            selected_idx = int(selection) - 1
            if selected_idx < 0 or selected_idx >= len(image_files):
                print("❌ Selección inválida, usando la primera imagen")
                selected_idx = 0
    except ValueError:
        print("❌ Entrada inválida, usando la primera imagen")
        selected_idx = 0
    
    test_image = image_files[selected_idx]
    print(f"\n🎯 Imagen seleccionada: {test_image.name}")
    
    # 4. Ejecutar pruebas
    print("\n" + "="*60)
    print("🧪 EJECUTANDO PRUEBAS")
    print("="*60)
    
    # Prueba 1: /predict con multipart
    success1 = test_predict_multipart(test_image)
    
    # Prueba 2: /predict-raw con base64
    success2 = test_predict_raw_base64(test_image)
    
    # Prueba 3: /predict con base64 (fallback)
    success3 = test_predict_base64(test_image)
    
    # 5. Resumen
    print("\n" + "="*60)
    print("📋 RESUMEN DE PRUEBAS")
    print("="*60)
    print(f"✅ /health: OK")
    print(f"{'✅' if success1 else '❌'} /predict (multipart): {'OK' if success1 else 'ERROR'}")
    print(f"{'✅' if success2 else '❌'} /predict-raw (base64): {'OK' if success2 else 'ERROR'}")
    print(f"{'✅' if success3 else '❌'} /predict (base64 fallback): {'OK' if success3 else 'ERROR'}")
    
    if success1 or success2 or success3:
        print("\n🎉 ¡Al menos un endpoint funciona correctamente!")
    else:
        print("\n⚠️ Todos los endpoints fallaron. Revisa el servidor.")

if __name__ == "__main__":
    main()