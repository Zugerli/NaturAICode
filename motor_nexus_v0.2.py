# motor_nexus_v0.4.py
import openai  # Para el razonamiento
import cv2     # Para la visión
import pyttsx3 # Para la voz

class Nexus:
    def __init__(self):
        self.engine_voz = pyttsx3.init()
        self.configurar_idioma('es-ES')  # Idioma por defecto al arrancar
        self.cap = None

        # Cargamos el clasificador de rostros nativo de OpenCV (Sin librerías obsoletas)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def configurar_idioma(self, codigo_idioma):
        # codigo_idioma recibe cadenas estilo 'es-ES', 'es-MX', 'en-US'
        voces = self.engine_voz.getProperty('voices')
        encontrado = False

        for voz in voces:
            # Comparamos ignorando mayúsculas/minúsculas con el estándar de Windows
            if codigo_idioma.lower() in voz.id.lower():
                self.engine_voz.setProperty('voice', voz.id)
                encontrado = True
                break

        if not encontrado:
            print(f"[Nexus Advertencia]: No se encontró la voz exacta para '{codigo_idioma}'. Usando voz activa.")

    def hablar(self, texto):
        print(f"[Nexus]: {texto}")
        self.engine_voz.say(texto)
        self.engine_voz.runAndWait()

    def ejecutar(self, comando):
        comando = comando.strip()

        # Procesar comando: configurar.idioma("es-ES")
        if "configurar.idioma" in comando:
            idioma = comando.split('"')[1]
            self.configurar_idioma(idioma)

        # Procesar comando: voz.decir("texto")
        elif "voz.decir" in comando:
            texto = comando.split('"')[1]
            self.hablar(texto)

        # Procesar comando: mirar.describir()
        elif "mirar.describir" in comando:
            self.hablar("Abriendo cámara para escanear el entorno.")
            self.cap = cv2.VideoCapture(0)

            # Dejar que la cámara ajuste la exposición de luz
            for _ in range(10):
                ret, frame = self.cap.read()

            if ret:
                # Convertir a escala de grises para el procesamiento del modelo
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Detectar rostros reales en la habitación
                rostros = self.face_cascade.detectMultiScale(gray, 1.1, 4)

                # Dibujar un recuadro verde por cada rostro hallado
                for (x, y, w, h) in rostros:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                cv2.imshow("Vista en tiempo real - Nexus-AI", frame)

                # Lógica de respuesta según la visión real de la IA
                num_rostros = len(rostros)
                if num_rostros == 1:
                    self.hablar("Hecho. Veo una persona frente a la computadora.")
                elif num_rostros > 1:
                    self.hablar(f"Hecho. Identifico a {num_rostros} personas en la habitación.")
                else:
                    self.hablar("He analizado el entorno. No detecto rostros en este momento, pero la habitación está despejada.")

                cv2.waitKey(4000)  # Muestra la ventana 4 segundos antes de cerrarse
                cv2.destroyAllWindows()

            self.cap.release()

    def probar(self, codigo_nexus):
        for linea in codigo_nexus.split('\n'):
            # Ignorar líneas vacías y comentarios de Nexus
            if linea.strip() and not linea.strip().startswith("//"):
                self.ejecutar(linea)

# ===================================================
# PRUEBA DE USUARIO (Zugerli)
# ===================================================
mi_app = """
configurar.idioma("es-ES")
voz.decir("Iniciando reconocimiento de entorno.")
mirar.describir()
"""

nexus = Nexus()
nexus.probar(mi_app)
