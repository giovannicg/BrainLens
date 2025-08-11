#!/usr/bin/env python3
"""
Script para crear un modelo compatible con el formato de entrada RGB
"""

import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB3
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
import os

def create_compatible_model():
    """Crear un modelo compatible con entrada RGB"""
    
    # Parámetros
    IMG_SIZE = 300
    NUM_CLASSES = 4
    
    # Crear modelo base
    base_model = EfficientNetB3(
        include_top=False,
        weights='imagenet',
        input_shape=(IMG_SIZE, IMG_SIZE, 3)
    )
    base_model.trainable = False
    
    # Crear modelo completo
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dropout(0.4)(x)
    x = Dense(NUM_CLASSES, activation="softmax")(x)
    
    model = Model(inputs=base_model.input, outputs=x)
    
    # Compilar modelo
    model.compile(
        optimizer=Adam(learning_rate=1e-4),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

def main():
    """Función principal"""
    print("🧠 Creando modelo compatible...")
    
    # Crear modelo
    model = create_compatible_model()
    
    # Guardar modelo
    output_path = "modelo_multiclase_compatible.h5"
    model.save(output_path)
    
    print(f"✅ Modelo guardado en: {output_path}")
    print(f"📊 Resumen del modelo:")
    model.summary()
    
    # Verificar que se puede cargar
    try:
        loaded_model = tf.keras.models.load_model(output_path)
        print("✅ Modelo se puede cargar correctamente")
    except Exception as e:
        print(f"❌ Error al cargar el modelo: {e}")

if __name__ == "__main__":
    main()


