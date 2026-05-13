# ==============================================================================
# LIBRERÍAS REQUERIDAS:
# pip install opencv-python pyttsx3 ollama openai SpeechRecognition pyaudio
# ==============================================================================

import cv2
import pyttsx3
import ollama
import locale
import speech_recognition as sr
from openai import OpenAI

class Nexus:
    def __init__(self):
        self.cap = None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.reconocedor = sr.Recognizer()

        # Configuración de Modelos
        self.modelo_local = "llama3:8b"
        self.cliente_ollama = ollama.Client()
        self.api_key_pago = None 
        self.client_pago = None

        # Tabla de idiomas nativos
        self.idiomas_soportados = {
            'es': 'es-ES', 'en': 'en-US', 'fr': 'fr-FR', 'it': 'it-IT', 'de': 'de-DE'
        }

        # Guardamos el idioma activo del sistema
        self.idioma_activo = self.detectar_idioma_natal()

    def detectar_idioma_natal(self):
        try:
            idioma_sistema, _ = locale.getdefaultlocale()
            prefijo = idioma_sistema.split('_')[0].lower() if idioma_sistema else 'en'
            return self.idiomas_soportados.get(prefijo, 'en-US')
        except Exception:
            return 'en-US'

    def hablar(self, texto, codigo_idioma=None):
        """ Inicializa y destruye el motor en cada llamada para evitar congelamientos de SAPI5 """
        # Si no se especifica un idioma, usamos el idioma activo global
        if not codigo_idioma:
            codigo_idioma = self.idioma_activo

        print(f"[Nexus - {codigo_idioma}]: {texto}")

        # Inicialización fresca del motor para limpiar buffers corruptos de Windows
        engine = pyttsx3.init()
        voces = engine.getProperty('voices')

        # Buscar la voz exacta instalada en el Windows de Zugerli
        for voz in voces:
            if codigo_idioma.lower() in voz.id.lower():
                engine.setProperty('voice', voz.id)
                break

        engine.say(texto)
        engine.runAndWait()
        engine.stop() # Forzamos el cierre inmediato del servicio de audio

    def razonar_hibrido(self, pregunta):
        try:
            respuesta = self.cliente_ollama.generate(model=self.modelo_local, prompt=pregunta)
            return respuesta['response']
        except Exception as e:
            return f"Error en cerebro local: {e}"

    def capturar_microfono(self):
        with sr.Microphone() as fuente:
            print("[Oído]: Escuchando... Habla ahora.")
            self.reconocedor.adjust_for_ambient_noise(fuente, duration=1)
            audio = self.reconocedor.listen(fuente)

            try:
                print("[Oído]: Procesando audio...")
                texto_escuchado = self.reconocedor.recognize_google(audio, language=self.idioma_activa if hasattr(self, 'idioma_activa') else "es-ES")
                print(f"[Usuario dijo]: {texto_escuchado}")
                return texto_escuchado
            except sr.UnknownValueError:
                self.hablar("No logré entender lo que dijiste.")
                return None
            except sr.RequestError:
                self.hablar("Problema de conexión en el módulo de oído.")
                return None

    def ejecutar(self, comando):
        comando = comando.strip()

        if "configurar.idioma" in comando:
            idioma = comando.split('"')[1]
            self.idioma_activo = idioma
            print(f"[Nexus]: Idioma cambiado globalmente a {idioma}")

        elif "voz.decir" in comando:
            texto = comando.split('"')[1]
            self.hablar(texto)

        elif "cerebro.razonar" in comando:
            pregunta = comando.split('"')[1]
            respuesta = self.razonar_hibrido(pregunta)
            self.hablar(respuesta)

        elif "escuchar.traducir" in comando:
            idioma_destino = comando.split('"')[1]
            self.hablar("Por favor, habla después de que se active el micrófono.")

            texto_humano = self.capturar_microfono()
            if texto_humano:
                prompt_traduccion = f"Traduce exactamente el siguiente texto al idioma cuya cultura es {idioma_destino}. Devuelve EXCLUSIVAMENTE la traducción, sin textos adicionales: '{texto_humano}'"
                traduccion = self.razonar_hibrido(prompt_traduccion).strip()

                # Pasamos explícitamente el idioma destino a la función hablar para que use la voz correcta
                self.hablar(traduccion, codigo_idioma=idioma_destino)

                # Confirmación final volviendo de forma segura a español
                self.hablar("Traducción completada con éxito.", codigo_idioma=self.detectar_idioma_natal())

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

    def probar(self, codigo_nexus):
        for linea in codigo_nexus.split('\n'):
            if linea.strip() and not linea.strip().startswith("//"):
                self.ejecutar(linea)

# ==============================================================================
# PRUEBA DE USUARIO (Zugerli)
# ==============================================================================
mi_app = """
configurar.idioma("es-ES")
escuchar.traducir(a: "en-US") // Prueba con "en-US"
"""

nexus = Nexus()
nexus.probar(mi_app)
