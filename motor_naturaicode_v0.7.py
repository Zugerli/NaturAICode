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

# Librerías nativas para la Interfaz Gráfica (UI)
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class Naic:
    def __init__(self):
        self.cap = None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.reconocedor = sr.Recognizer()

        # Configuración de Modelos Locales
        self.modelo_local = "llama3:8b"
        self.cliente_ollama = ollama.Client()
        self.api_key_pago = None 
        self.client_pago = None

        self.idiomas_soportados = {
            'es': 'es-ES', 'en': 'en-US', 'fr': 'fr-FR', 'it': 'it-IT', 'de': 'de-DE'
        }
        self.idioma_activa = self.detectar_idioma_natal()

        # Variables de control para la interfaz gráfica
        self.root = None
        self.lbl_video = None
        self.txt_consola = None

    def detectar_idioma_natal(self):
        try:
            idioma_sistema, _ = locale.getdefaultlocale()
            prefijo = idioma_sistema.split('_').lower() if idioma_sistema else 'en'
            return self.idiomas_soportados.get(prefijo, 'en-US')
        except Exception:
            return 'en-US'

    def hablar(self, texto, codigo_idioma=None):
        if not codigo_idioma:
            codigo_idioma = self.idioma_activa

        self.actualizar_consola(f"[Naic]: {texto}")

        engine = pyttsx3.init()
        voces = engine.getProperty('voices')
        for voz in voces:
            if codigo_idioma.lower() in voz.id.lower():
                engine.setProperty('voice', voz.id)
                break
        engine.say(texto)
        engine.runAndWait()
        engine.stop()

    def actualizar_consola(self, texto):
        """ Imprime en terminal y escribe en la consola visual si está activa """
        print(texto)
        if self.txt_consola:
            self.txt_consola.insert(tk.END, texto + "\n")
            self.txt_consola.see(tk.END)
            self.root.update_idletasks()

    def razonar_hibrido(self, pregunta):
        try:
            respuesta = self.cliente_ollama.generate(model=self.modelo_local, prompt=pregunta)
            return respuesta['response']
        except Exception as e:
            return f"Error en cerebro local: {e}"

    def capturar_microfono(self):
        with sr.Microphone() as fuente:
            self.actualizar_consola("[Oído]: Escuchando... Habla ahora.")
            self.reconocedor.adjust_for_ambient_noise(fuente, duration=1)
            audio = self.reconocedor.listen(fuente)

            try:
                self.actualizar_consola("[Oído]: Procesando audio...")
                texto_escuchado = self.reconocedor.recognize_google(audio, language="es-ES")
                self.actualizar_consola(f"[Usuario]: {texto_escuchado}")
                return texto_escuchado
            except sr.UnknownValueError:
                self.hablar("No logré entender lo que dijiste.")
                return None
            except sr.RequestError:
                self.actualizar_consola("[Error]: Problema de conexión en el módulo de oído.")
                return None

    def UI_activar_microfono(self):
        """ Acción vinculada al botón de la interfaz gráfica """
        texto_humano = self.capturar_microfono()
        if texto_humano:
            # Por defecto lo traduce a alemán para mantener la exitosa prueba v0.6.1
            prompt_traduccion = f"Traduce exactamente el siguiente texto al alemán (de-DE). Devuelve EXCLUSIVAMENTE la traducción: '{texto_humano}'"
            traduccion = self.razonar_hibrido(prompt_traduccion).strip()

            self.hablar(traduccion, codigo_idioma="de-DE")
            self.hablar("Traducción completada con éxito.", codigo_idioma=self.detectar_idioma_natal())

    def UI_actualizar_camara(self):
        """ Captura frames continuamente y los renderiza en la interfaz """
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Procesamiento visual de rostros en tiempo real
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                rostros = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                for (x, y, w, h) in rostros:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                # Conversión de OpenCV (BGR) a formato compatible con Tkinter (RGB)
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                imgtk = ImageTk.PhotoImage(image=img)

                self.lbl_video.imgtk = imgtk
                self.lbl_video.configure(image=imgtk)

            # Re-ejecutar esta función cada 20 milisegundos para mantener el flujo de video vivo
            self.lbl_video.after(20, self.UI_actualizar_camara)

    def iniciar_interfaz_grafica(self):
        """ Construye la ventana del Naic Studio """
        self.root = tk.Tk()
        self.root.title("Naic-AI Studio - v0.7")
        self.root.geometry("900x550")
        self.root.configure(bg="#1e1e1e") # Estética oscura industrial

        # Estilo para los componentes modernos
        style = ttk.Style()
        style.theme_use('clam')

        # CONTENEDOR PRINCIPAL IZQUIERDO (Visión de Cámara)
        frame_izq = tk.Frame(self.root, bg="#1e1e1e")
        frame_izq.pack(side=tk.LEFT, padx=15, pady=15, fill=tk.BOTH, expand=True)

        self.lbl_video = tk.Label(frame_izq, bg="#000000")
        self.lbl_video.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Encender la cámara interna para la interfaz de video continua
        self.cap = cv2.VideoCapture(0)

        # CONTENEDOR PRINCIPAL DERECHO (Consola y Mandos)
        frame_der = tk.Frame(self.root, bg="#2d2d2d", width=350)
        frame_der.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(0, 15), pady=15)

        lbl_panel = tk.Label(frame_der, text="CONSOLA DE LOGS", font=("Arial", 10, "bold"), fg="#ffffff", bg="#2d2d2d")
        lbl_panel.pack(pady=10)

        # Consola de Texto Oscura
        self.txt_consola = tk.Text(frame_der, bg="#121212", fg="#00ff00", font=("Consolas", 9), insertbackground="white")
        self.txt_consola.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Botón Interactuable para el Estudiante (Disparador del Micrófono)
        btn_micro = tk.Button(
            frame_der, text="🎤 ACTIVAR MICRÓFONO (Escuchar/Traducir)",
            font=("Arial", 10, "bold"), bg="#4CAF50", fg="white",
            activebackground="#45a049", command=self.UI_activar_microfono
        )
        btn_micro.pack(fill=tk.X, padx=10, pady=15)

        # Lanzar la actualización paralela del bucle de video y la app de escritorio
        self.UI_actualizar_camara()
        self.actualizar_consola("[Sistema]: Interfaz gráfica inicializada correctamente.")

        self.root.mainloop()

        # Apagar recursos ordenadamente al cerrar la ventana
        if self.cap:
            self.cap.release()

    def ejecutar(self, comando):
        comando = comando.strip()

        if "crear_interfaz" in comando:
            self.iniciar_interfaz_grafica()

        elif "voz.decir" in comando:
            texto = comando.split('"')
            self.hablar(texto)

    def probar(self, codigo_naic):
        for linea in codigo_naic.split('\n'):
            if linea.strip() and not linea.strip().startswith("//"):
                self.ejecutar(linea)

# ==============================================================================
# PRUEBA DE USUARIO (Zugerli)
# ==============================================================================
mi_app = """
voz.decir("Cargando la interfaz gráfica de usuario.")
crear_interfaz("completa")
"""

naic = Naic()
naic.probar(mi_app)
