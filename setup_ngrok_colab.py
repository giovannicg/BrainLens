# SCRIPT PARA CONFIGURAR NGROK EN TU NOTEBOOK DE COLAB
# =====================================================

print("🔧 CONFIGURACIÓN DE NGROK PARA COLAB")
print("=" * 50)

print("""
📋 PASOS PARA CONFIGURAR NGROK:

1️⃣ INSTALAR NGROK EN TU NOTEBOOK:
   !pip install pyngrok

2️⃣ EJECUTAR ESTE CÓDIGO EN UNA NUEVA CELDA:
""")

print("""
# Configurar ngrok
from pyngrok import ngrok

# Exponer el puerto 8081 (donde está tu servidor Flask)
public_url = ngrok.connect(8081)
print(f"🌐 URL pública de ngrok: {public_url}")

# La URL será algo como: https://abc123.ngrok.io
# Copia esta URL y úsala en el siguiente paso
""")

print("""
3️⃣ ACTUALIZAR EL SERVICIO DE COLAB:
   Una vez que tengas la URL de ngrok, ejecuta este comando:
""")

print("""
curl -X POST http://localhost:8004/configure -H "Content-Type: application/json" \\
  -d '{"notebook_url": "TU_URL_DE_NGROK_AQUI"}'
""")

print("""
4️⃣ PROBAR LA CONEXIÓN:
   curl -X GET TU_URL_DE_NGROK_AQUI/health
""")

print("""
⚠️ IMPORTANTE:
- La URL de ngrok cambia cada vez que reinicies el notebook
- Necesitarás actualizar la configuración cada vez
- ngrok es gratuito pero tiene limitaciones de uso
""")

print("""
🎯 ALTERNATIVA MÁS SIMPLE:
Si prefieres probar localmente primero, puedes:
1. Ejecutar el notebook en tu máquina local
2. Usar http://localhost:8081/predict en el servicio de Colab
""") 