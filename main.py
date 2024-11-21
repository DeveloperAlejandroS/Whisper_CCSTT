import whisper

# Cargar el modelo
model = whisper.load_model("base")

# Transcribir el audio
result = model.transcribe("300000572722447.wav", language="es")
print(result['text'])
