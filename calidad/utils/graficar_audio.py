import librosa
import librosa.display
import matplotlib.pyplot as plt

# Ruta a tu archivo de audio
audio_path = "C:/Users/jmoreno/Downloads/Llamadas_aseco/buenas/2.mpeg"

# Cargar audio
y, sr = librosa.load(audio_path, sr=None)

# Graficar
plt.figure(figsize=(15, 4))
librosa.display.waveshow(y, sr=sr, alpha=0.7)
plt.title("Forma de onda del audio")
plt.xlabel("Tiempo (s)")
plt.ylabel("Amplitud")
plt.tight_layout()
plt.show()
