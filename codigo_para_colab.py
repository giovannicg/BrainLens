# CÓDIGO PARA AGREGAR A TU NOTEBOOK DE COLAB
# ==============================================

# Instalar dependencias si no están instaladas
!pip install flask flask-cors pyngrok

# Importar librerías
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import base64
import io
from PIL import Image
import numpy as np
from tensorflow.keras.preprocessing import image
from datetime import datetime

# Crear aplicación Flask
app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud"""
    return jsonify({
        'status': 'healthy',
        'service': 'colab-brainlens',
        'model_loaded': 'model' in globals(),
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint para predicción usando tu código exacto"""
    try:
        # Obtener datos de la imagen
        data = request.get_json()
        image_data = data.get('image_data')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        print("🔄 Procesando imagen recibida...")
        
        # Decodificar imagen base64
        image_bytes = base64.b64decode(image_data)
        
        # Guardar imagen temporalmente
        temp_path = "/tmp/temp_image.png"
        with open(temp_path, 'wb') as f:
            f.write(image_bytes)
        
        # TU CÓDIGO EXACTO DE PROCESAMIENTO
        IMG_SIZE = 300
        
        # 2️⃣ Cargar y preprocesar la imagen
        img = image.load_img(temp_path, target_size=(IMG_SIZE, IMG_SIZE))
        img_array = image.img_to_array(img)
        img_array = img_array / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        print(f"📸 Imagen preprocesada: {img_array.shape}")
        
        # 3️⃣ Predecir (usar tu modelo)
        predicciones = model.predict(img_array, verbose=0)
        
        # 4️⃣ Interpretar resultado
        clase_predicha = np.argmax(predicciones, axis=1)[0]
        confianza = float(predicciones[0][clase_predicha])
        
        print(f"Clase predicha: {clase_predicha}")
        print(f"Probabilidades: {predicciones}")
        
        # Mapear clases (ajusta según tu modelo)
        classes = ['glioma', 'meningioma', 'no_tumor', 'pituitary']
        es_tumor = clase_predicha != 2  # índice 2 = 'no_tumor'
        
        # Crear resultado
        result = {
            'es_tumor': es_tumor,
            'clase_predicha': classes[clase_predicha],
            'confianza': confianza,
            'probabilidades': {
                clase: float(prob) 
                for clase, prob in zip(classes, predicciones[0])
            },
            'recomendacion': "⚠️ Se ha detectado un tumor cerebral. Se recomienda consultar con un médico especialista inmediatamente." if es_tumor else "✅ No se ha detectado ningún tumor. Continuar con revisiones rutinarias.",
            'timestamp': datetime.utcnow().isoformat()
        }
        
        print(f"✅ Predicción completada: {result['clase_predicha']} ({confianza:.2%})")
        
        # Limpiar archivo temporal
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify({
            'status': 'success',
            'prediction': result
        })
        
    except Exception as e:
        print(f"❌ Error en predicción: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# Iniciar servidor en background
def run_server():
    """Ejecutar servidor Flask"""
    app.run(host='0.0.0.0', port=8081)

print("🚀 Iniciando servidor API...")
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

print("✅ Servidor API iniciado en puerto 8081")
print("📡 Endpoints disponibles:")
print("   - GET  /health   - Verificar estado del servicio")
print("   - POST /predict  - Procesar imagen")

# Configurar ngrok para exponer el puerto
print("\n🌐 Configurando ngrok...")
try:
    from pyngrok import ngrok
    
    # Exponer el puerto 8081
    public_url = ngrok.connect(8081)
    print(f"✅ URL pública de ngrok: {public_url}")
    print(f"🔗 Endpoint público: {public_url}/predict")
    
    print("\n📋 Para configurar tu aplicación Docker:")
    print(f"curl -X POST http://localhost:8004/configure -H \"Content-Type: application/json\" -d '{{\"notebook_url\": \"{public_url}\"}}'")
    
except Exception as e:
    print(f"❌ Error configurando ngrok: {str(e)}")
    print("💡 Puedes configurar ngrok manualmente más tarde")

# Esperar un momento para que el servidor inicie
import time
time.sleep(3)

print("\n🎉 ¡Servidor listo para recibir imágenes!")
print("📝 Recuerda: La URL de ngrok cambia cada vez que reinicies el notebook") 