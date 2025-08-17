# CÓDIGO PARA AGREGAR AL FINAL DE TU NOTEBOOK DE COLAB
# =====================================================

# Celda 1: Instalar dependencias
!pip install pyngrok flask flask-cors

# Celda 2: Configurar ngrok con token
from pyngrok import ngrok
import flask
from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import base64

# Configurar tu token de autenticación de ngrok
# ngrok.set_auth_token('TU_TOKEN_AQUI')  # Reemplaza con tu token real

# Celda 3: Crear servidor Flask
app = Flask(__name__)
CORS(app)

# Cargar modelo (ajusta la ruta según tu notebook)
model = tf.keras.models.load_model('modelo_multiclase_final.keras', compile=False)
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "colab-notebook"})

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Obtener imagen en base64
        data = request.json
        image_data = base64.b64decode(data['image_data'])
        
        # Preprocesar imagen
        img = Image.open(io.BytesIO(image_data))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img = img.resize((300, 300))  # Tamaño usado en entrenamiento
        img_array = np.array(img) / 255.0  # Normalizar
        img_array = np.expand_dims(img_array, axis=0)  # Añadir dimensión batch
        
        # Hacer predicción
        predictions = model.predict(img_array, verbose=0)
        
        # Mapear clases (según tu entrenamiento)
        classes = ['glioma', 'meningioma', 'notumor', 'pituitary']
        predicted_class_idx = np.argmax(predictions[0])
        predicted_class = classes[predicted_class_idx]
        confidence = float(predictions[0][predicted_class_idx])
        
        # Crear resultado
        result = {
            "es_tumor": predicted_class != "notumor",
            "clase_predicha": predicted_class,
            "confianza": confidence,
            "probabilidades": {
                classes[i]: float(predictions[0][i]) for i in range(len(classes))
            }
        }
        
        # Agregar recomendación
        if predicted_class == "notumor":
            result["recomendacion"] = "✅ No se ha detectado ningún tumor. Continuar con revisiones rutinarias."
        else:
            result["recomendacion"] = f"⚠️ Se ha detectado un posible tumor de tipo {predicted_class}. Se recomienda consultar con un especialista."
        
        return jsonify({"prediction": result})
        
    except Exception as e:
        print(f"Error en predict: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Celda 4: Iniciar servidor con ngrok
if __name__ == '__main__':
    # Exponer con ngrok
    public_url = ngrok.connect(8081)
    print(f"🌐 URL pública: {public_url}")
    
    # Iniciar servidor Flask
    app.run(host='0.0.0.0', port=8081)
