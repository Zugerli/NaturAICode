# Este código permitiría que alguien escriba un archivo .naic y el motor lo ejecute.
# motor_naic_v0.3.py
import cv2
import pyttsx3

class Naic:
    def __init__(self):
        self.engine_voz = pyttsx3.init()
        self.configurar_idioma('es') # Forzamos español
        self.cap = None

    def configurar_idioma(self, prefijo_idioma):
        voces = self.engine_voz.getProperty('voices')
        for voz in voces:
            if prefijo_idioma in voz.languages or prefijo_idioma in voz.id.lower():
                self.engine_voz.setProperty('voice', voz.id)
                break

    def hablar(self, texto):
        print(f"[Naic]: {texto}")
        self.engine_voz.say(texto)
        self.engine_voz.runAndWait()

    def ejecutar(self, comando):
        comando = comando.strip().lower()

        if "voz.decir" in comando:
            texto = comando.split('"')[1]
            self.hablar(texto)

        elif "mirar.describir" in comando:
            self.hablar("Activando visión para describir la habitación.")
            self.cap = cv2.VideoCapture(0) # Abre la cámara
            ret, frame = self.cap.read()
            if ret:
                cv2.imshow("Vista de Naic-AI", frame)
                # Aquí en el futuro enviamos el 'frame' a un modelo como Gemini
                self.hablar("Veo una habitación. La iluminación es adecuada y detecto objetos frente a mí.")
                cv2.waitKey(2000) # Muestra la imagen 2 segundos
                cv2.destroyAllWindows()
            self.cap.release()

    def probar(self, codigo_naic):
        for linea in codigo_naic.split('\n'):
            if linea.strip() and not linea.startswith("//"):
                self.ejecutar(linea)

# PRUEBA DE ZUGERLI
mi_app = """
voz.decir("Hola, voy a echar un vistazo a tu habitación.")
mirar.describir()
"""

naic = Naic()
naic.probar(mi_app)