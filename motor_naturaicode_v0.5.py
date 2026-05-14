# motor_naic_v0.5.py
import cv2
import pyttsx3
import ollama
from openai import OpenAI  # Para la opción de pago (por ejemplo, GPT-4o o Claude)

class Naic:
    def __init__(self):
        self.engine_voz = pyttsx3.init()
        self.configurar_idioma('es-ES')
        self.cap = None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # Configuración de Modelos (El estudiante puede cambiar esto)
        self.modelo_local = "llama3:8b"
        self.api_key_pago = None  # Reemplazar con clave real si se desea activar el modelo de pago
        self.client_pago = None

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
        print(f"[Cerebro]: Procesando la petición: '{pregunta}'")

        # Intentar resolver con el modelo LOCAL gratuito primero
        try:
            print(f"[Cerebro Local]: Pensando con {self.modelo_local}...")
            respuesta = ollama.generate(model=self.modelo_local, prompt=pregunta)
            text_res = respuesta['response']

            # Lógica de derivación: Si la respuesta local es muy corta o el usuario pide explícitamente complejidad
            if "complejo" in pregunta.lower() and self.api_key_pago:
                print("[Cerebro]: Detectada complejidad alta. Derivando al modelo de pago...")
                return self.razonar_pago(pregunta)

            return f"[Local] {text_res}"

        except Exception as e:
            # Si el modelo local falla o no está encendido, intentamos usar el de pago si está disponible
            print(f"[Naic Advertencia]: Error en modelo local.")
            if self.api_key_pago:
                print("[Cerebro]: Derivando automáticamente al modelo en la nube...")
                return self.razonar_pago(pregunta)
            else:
                return "Error: El cerebro local no responde y no hay un cerebro de pago configurado. ¿Olvidaste encender Ollama?"

    def razonar_pago(self, pregunta):
        if not self.client_pago:
            self.client_pago = OpenAI(api_key=self.api_key_pago)

        try:
            completion = self.client_pago.chat.completions.create(
                model="gpt-4o-mini", # Un modelo de pago ultra eficiente
                messages=[{"role": "user", "content": pregunta}]
            )
            return f"[Nube] {completion.choices[0].message.content}"
        except Exception as e:
            return f"Error crítico en el modelo de pago: {str(e)}"

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

# ===================================================
# PRUEBA DE USUARIO (Zugerli)
# ===================================================
mi_app = """
configurar.idioma("es-ES")
cerebro.razonar("Explícame brevemente qué es la gravedad de forma sencilla")
"""

naic = Naic()
naic.probar(mi_app)
