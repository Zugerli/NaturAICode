# ==============================================================================
# LIBRERÍAS REQUERIDAS (Ejecutar antes en la terminal):
# pip install opencv-python pyttsx3 ollama openai SpeechRecognition pyaudio
# ==============================================================================

import cv2
import pyttsx3
import ollama
import locale
import speech_recognition as sr
from openai import OpenAI

class Naic:
    def __init__(self):
        self.engine_voz = pyttsx3.init()
        self.cap = None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # Reconocedor de voz para el micrófono
        self.reconocedor = sr.Recognizer()

        # Configuración Local-Local (¡Probada y exitosa!)
        self.modelo_local = "llama3:8b"
        self.cliente_ollama = ollama.Client() # Conexión local por defecto

        self.api_key_pago = None 
        self.client_pago = None

        self.idiomas_soportados = {
            'es': 'es-ES', 'en': 'en-US', 'fr': 'fr-FR', 'it': 'it-IT', 'de': 'de-DE'
        }
        self.detectar_y_configurar_idioma_natal()

    def detectar_y_configurar_idioma_natal(self):
        try:
            idioma_sistema, _ = locale.getdefaultlocale()
            prefijo = idioma_sistema.split('_')[0].lower() if idioma_sistema else 'en'
            codigo_windows = self.idiomas_soportados.get(prefijo, 'en-US')
            self.configurar_idioma(codigo_windows)
            print(f"[Naic]: Idioma del sistema configurado: {codigo_windows}")
        except Exception:
            self.configurar_idioma('en-US')

    def configurar_idioma(self, codigo_idioma):
        voces = self.engine_voz.getProperty('voices')
        for voz in voces:
            if codigo_idioma.lower() in voz.id.lower():
                self.engine_voz.setProperty('voice', voz.id)
                break

    def hablar(self, texto):
        print(f"[Naic]: {texto}")
        self.engine_voz.say(texto)
        self.engine_voz.runAndWait()

    def razonar_hibrido(self, pregunta):
        try:
            respuesta = self.cliente_ollama.generate(model=self.modelo_local, prompt=pregunta)
            return respuesta['response']
        except Exception as e:
            return f"Error en cerebro local: {e}"

    def capturar_microfono(self):
        with sr.Microphone() as fuente:
            print("[Oído]: Escuchando... Habla ahora.")
            # Ajustar el ruido ambiental automáticamente
            self.reconocedor.adjust_for_ambient_noise(fuente, duration=1)
            audio = self.reconocedor.listen(fuente)

            try:
                # Transcribe el audio usando el motor nativo de Google (gratuito)
                print("[Oído]: Procesando audio...")
                texto_escuchado = self.reconocedor.recognize_google(audio, language="es-ES")
                print(f"[Usuario dijo]: {texto_escuchado}")
                return texto_escuchado
            except sr.UnknownValueError:
                self.hablar("No logré entender lo que dijiste, ¿podrías repetirlo?")
                return None
            except sr.RequestError:
                self.hablar("Problema de conexión con el sistema de oído.")
                return None

    def ejecutar(self, comando):
        comando = comando.strip()

        if "configurar.idioma" in comando:
            idioma = comando.split('"')[1]
            self.configurar_idioma(idioma)

        elif "voz.decir" in comando:
            texto = comando.split('"')[1]
            self.hablar(texto)

        elif "cerebro.razonar" in comando:
            pregunta = comando.split('"')[1]
            respuesta = self.razonar_hibrido(pregunta)
            self.hablar(respuesta)

        # NUEVO COMANDO MÁGICO v0.6
        elif "escuchar.traducir" in comando:
            idioma_destino = comando.split('"')[1]
            self.hablar(f"Por favor, habla después de que se active el micrófono.")

            texto_humano = self.capturar_microfono()
            if texto_humano:
                # Usamos el cerebro de Ollama para hacer la traducción de forma inteligente
                prompt_traduccion = f"Traduce exactamente el siguiente texto al idioma {idioma_destino}. Devuelve SOLO la traducción, nada más: '{texto_humano}'"
                traduccion = self.razonar_hibrido(prompt_traduccion)

                # Cambiamos temporalmente la voz de Naic para que pronuncie bien el idioma destino
                if "ingles" in idioma_destino.lower() or "english" in idioma_destino.lower():
                    self.configurar_idioma("en-US")

                self.hablar(traduccion)

                # Restauramos a español
                self.detectar_y_configurar_idioma_natal()

        elif "mirar.describir" in comando:
            self.hablar("Abriendo cámara para escaneo rápido.")
            self.cap = cv2.VideoCapture(0)
            ret, frame = self.cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                rostros = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                if len(rostros) > 0:
                    self.hablar(f"Veo {len(rostros)} rostro(s) humano(s).")
                else:
                    self.hablar("No detecto humanos ahora mismo.")
            self.cap.release()

    def probar(self, codigo_naic):
        for linea in codigo_naic.split('\n'):
            if linea.strip() and not linea.strip().startswith("//"):
                self.ejecutar(linea)

# ==============================================================================
# PRUEBA DE USUARIO (Zugerli)
# ==============================================================================
mi_app = """
escuchar.traducir(a: "ingles")
"""

naic = Naic()
naic.probar(mi_app)
