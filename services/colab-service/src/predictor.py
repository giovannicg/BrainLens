import os
import logging
import numpy as np
import tensorflow as tf
from PIL import Image

def load_models_from_dir(directory):
	"""Carga todos los modelos .keras desde un directorio, filtrando por input_shape."""
	models = []
	for fname in os.listdir(directory):
		if fname.endswith('.keras'):
			path = os.path.join(directory, fname)
			try:
				model = tf.keras.models.load_model(path)
				input_shape = model.input_shape
				if len(input_shape) == 4 and input_shape[-1] == 3:
					models.append(model)
					logging.info(f"Modelo cargado: {path}")
				else:
					logging.warning(f"Modelo ignorado por input_shape incompatible: {path} (input_shape={input_shape})")
			except Exception as e:
				logging.error(f"Error cargando modelo {path}: {e}")
	return models

def preprocess_image(pil_img, input_shape):
	"""Preprocesa la imagen PIL según el input_shape del modelo."""
	if len(input_shape) == 4:
		_, h, w, c = input_shape
	else:
		h, w, c = 224, 224, 3
	img_model = pil_img.resize((w, h))
	if c == 1:
		img_model = img_model.convert("L")
	else:
		img_model = img_model.convert("RGB")
	arr_model = np.array(img_model) / 255.0
	if c == 1 and arr_model.ndim == 2:
		arr_model = np.expand_dims(arr_model, axis=-1)
	arr_model = np.expand_dims(arr_model, axis=0)
	return arr_model

def predict_with_models(models, pil_img, post=False, class_names=None):
	"""Realiza predicción con una lista de modelos. Si post=True, devuelve clases y scores."""
	predictions = []
	scores = []
	for model in models:
		arr_model = preprocess_image(pil_img, model.input_shape)
		try:
			pred = model.predict(arr_model)
			if post and class_names:
				pred_idx = int(np.argmax(pred[0]))
				pred_class = class_names[pred_idx]
				score = float(pred[0][pred_idx])
				predictions.append(pred_class)
				scores.append(score)
			else:
				score = float(pred.flatten()[0])
				scores.append(score)
		except Exception as e:
			logging.error(f"Error en predicción con modelo {model.name}: {e}")
	return (predictions, scores) if post else scores
