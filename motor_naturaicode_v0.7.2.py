# ==============================================================================
# LIBRERÍAS REQUERIDAS:
# pip install opencv-python pyttsx3 ollama openai SpeechRecognition pyaudio
# ==============================================================================

# ==============================================================================
# MOTOR NAIC v0.7.2 
# ==============================================================================
import sys
import locale
import cv2
import pyttsx3
import speech_recognition as sr
import ollama
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class Naic:
    def __init__(self):
        self.cap = None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.reconocedor = sr.Recognizer()

        self.modelo_local = "llama3:8b"
        self.cliente_ollama = ollama.Client()

        # --- LÓGICA DINÁMICA DE VOCES ---
        self.idiomas_soportados = {}  # Se llenará dinámicamente: {'es-ES': <Voice Object>, ...}
        self.mapeo_nombres = {        # Para traducir nombres comunes a códigos de lenguaje
            'español': 'spanish', 'spanish': 'es', 'inglés': 'en', 'english': 'en',
            'francés': 'fr', 'french': 'fr', 'alemán': 'de', 'german': 'de', 'deutsch': 'de', 'italiano': 'it'
        }
        
        self.escanear_voces_del_sistema()
        self.idioma_activa = self.detectar_idioma_natal()

        # UI y Control
        self.root = None
        self.lbl_video = None
        self.txt_consola = None
        self.btn_micro = None
        self.contador_frames = 0
        self.rostros_detectados_cache = []

    def escanear_voces_del_sistema(self):
        """ Escanea voces reales y las mapea en self.idiomas_soportados """
        engine = pyttsx3.init()
        voces = engine.getProperty('voices')
        
        print("\n--- [SISTEMA DE VOCES DETECTADO] ---")
        for voice in voces:
            # pyttsx3 devuelve una lista en voice.languages (ej: ['es_ES'])
            for lang in voice.languages:
                # Normalizamos a formato 'es-ES' o 'es' dependiendo del OS
                lang_code = lang.replace('_', '-').lower()
                self.idiomas_soportados[lang_code] = voice
                print(f" > Detectado: {lang_code} (Voz: {voice.name})")
        print("------------------------------------\n")

    def obtener_prefijo_idioma():
        # --- DETECCIÓN PARA WINDOWS (Nativo y Forzado BCP-47) ---
        if sys.platform == 'win32':
            import ctypes
        
            # Declaramos GetUserDefaultLocaleName (Devuelve siempre el tag corto de idioma: es-AR, en-US, etc.)
            ctypes.windll.kernel32.GetUserDefaultLocaleName.argtypes = [ctypes.c_wchar_p, ctypes.c_int]
            ctypes.windll.kernel32.GetUserDefaultLocaleName.restype = ctypes.c_int
        
            # El tamaño recomendado por Microsoft es LOCALE_NAME_MAX_LENGTH (85)
            buf = ctypes.create_unicode_buffer(85)
            resultado = ctypes.windll.kernel32.GetUserDefaultLocaleName(buf, 85)
            print(f"resultado de obtener prefijo idioma: {resultado}")
            if resultado > 0:
                # .value nos da la cadena Unicode limpia y directa (ej: "es-AR")
                return buf.value.lower().strip()
            
        # --- DETECCIÓN PARA LINUX / MACOS (Sin métodos obsoletos) ---
        try:
            locale.setlocale(locale.LC_ALL, '')
            idioma_posix, _ = locale.getlocale()
            
            if idioma_posix:
                # Extraemos la parte del idioma previa al punto y reemplazamos guiones bajos
                solo_idioma = idioma_posix.split('.')[0]
                # print(f"solo_idioma: {solo_idioma}")
                return solo_idioma.replace('_', '-').lower()
        except Exception:
            pass
        return 'en-us'  # Fallback definitivo en caso de error

    def detectar_idioma_natal(self):
        """ Detecta el idioma de Windows y verifica si tenemos voz para él """
        try:
            prefijo = obtener_prefijo_idioma() # Ya te garantiza el formato 'es-ar' o 'es-es'
            print(f"Idioma del sistema: {prefijo}")
            # Intentamos coincidencia exacta (es-es) o parcial (es)
            for code in self.idiomas_soportados:
                if prefijo.startswith(code) or code.startswith(prefijo.split('-')[0]):
                        return code
#            return 'en-us' # Fallback
        except Exception:
            return 'en-us'

    def hablar(self, texto, codigo_idioma=None):
        """ 
        Habla en el idioma solicitado si la voz existe. 
        Si no existe, usa el idioma_activa. 
        """
        if not codigo_idioma:
            codigo_idioma = self.idioma_activa

        self.actualizar_consola(f"[Naic]: {texto}")

        engine = pyttsx3.init()
        
        # Buscamos la mejor coincidencia de voz para el código solicitado
        voz_encontrada = None
        for code, voice_obj in self.idiomas_soportados.items():
            if codigo_idioma.lower() in code:
                voz_encontrada = voice_obj.id
                break
        
        if voz_encontrada:
            engine.setProperty('voice', voz_encontrada)
        else:
            self.actualizar_consola(f"[⚠️] Voz para '{codigo_idioma}' no instalada. Usando natal.")
            # Intentar usar la voz natal guardada
            if self.idioma_activa in self.idiomas_soportados:
                engine.setProperty('voice', self.idiomas_soportados[self.idioma_activa].id)

        engine.say(texto)
        engine.runAndWait()
        engine.stop()

    def actualizar_consola(self, texto):
        print(texto)
        if self.txt_consola:
            self.txt_consola.insert(tk.END, texto + "\n")
            self.txt_consola.see(tk.END)
            self.root.update_idletasks()

    def UI_activar_microfono(self):
        self.btn_micro.config(state=tk.DISABLED, text="⏳ ESCUCHANDO...")
        self.root.update_idletasks()

        with sr.Microphone() as fuente:
            self.reconocedor.adjust_for_ambient_noise(fuente, duration=0.8)
            audio = self.reconocedor.listen(fuente)
            
            try:
                # Preguntar idioma destino
                preguntar_idioma = "¿A qué idioma quieres traducir?"
                if self.idioma_activa == "es-es":
                    self.hablar(preguntar_idioma)  
                else:
                    prompt = f"Traduce al {self.idioma_activa}, devuelve sólo la traducción: '{preguntar_idioma}'"
                    respuesta = self.cliente_ollama.generate(model=self.modelo_local, prompt=prompt)
                    traduccion = respuesta['response'].strip()
                    self.hablar(traduccion)

                idioma_escuchado = self.reconocedor.recognize_google(audio, language=self.idioma_activa)
                idioma_traducir = idioma_escuchado

                if idioma_escuchado == '': 
                    idioma_escrito = txt_consola.input("Escribe el idioma (ej: alemán, inglés): ").lower()
                    idioma_traducir = idioma_escrito

                texto_humano = self.reconocedor.recognize_google(audio, language=self.idioma_activa)
                self.actualizar_consola(f"[Usuario]: {texto_humano}")

                # Mapear nombre a código (alemán -> de)
                codigo_dest = self.mapeo_nombres.get(idioma_traducir, 'en')

                # Verificar si tenemos la voz antes de traducir
                if any(codigo_dest in c for c in self.idiomas_soportados):
                    prompt = f"Traduce al {idioma_traducir}, devuelve solo la traducción: '{texto_humano}'"
                    respuesta = self.cliente_ollama.generate(model=self.modelo_local, prompt=prompt)
                    traduccion = respuesta['response'].strip()
                    
                    self.hablar(traduccion, codigo_idioma=codigo_dest)
                else:
                    self.actualizar_consola(f"[Error] No tienes instalada la voz para: {idioma_traducir}")
                    self.hablar(f"No puedo hablar en {idioma_traducir} porque la voz no está en Windows.")

            except Exception as e:
                self.actualizar_consola(f"[Oído]: No se detectó voz o hubo un error: {e}")

        self.btn_micro.config(state=tk.NORMAL, text="🎤 ACTIVAR MICRÓFONO")

    def UI_actualizar_camara(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.contador_frames += 1
                if self.contador_frames % 4 == 0:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    self.rostros_detectados_cache = self.face_cascade.detectMultiScale(gray, 1.2, 4)
                for (x, y, w, h) in self.rostros_detectados_cache:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                imgtk = ImageTk.PhotoImage(image=img)
                self.lbl_video.imgtk = imgtk
                self.lbl_video.configure(image=imgtk)
            self.lbl_video.after(15, self.UI_actualizar_camara)

    def iniciar_interfaz_grafica(self):
        self.root = tk.Tk()
        self.root.title("Naic-AI Studio v0.7.3 - Dynamic Voice Engine")
        self.root.geometry("900x550")
        self.root.configure(bg="#1e1e1e")

        frame_izq = tk.Frame(self.root, bg="#1e1e1e")
        frame_izq.pack(side=tk.LEFT, padx=15, pady=15, fill=tk.BOTH, expand=True)

        self.lbl_video = tk.Label(frame_izq, bg="#000000")
        self.lbl_video.pack(fill=tk.BOTH, expand=True)

        self.cap = cv2.VideoCapture(0)
        
        frame_der = tk.Frame(self.root, bg="#2d2d2d", width=350)
        frame_der.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(0, 15), pady=15)

        self.txt_consola = tk.Text(frame_der, bg="#121212", fg="#00ff00", font=("Consolas", 9))
        self.txt_consola.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.btn_micro = tk.Button(frame_der, text="🎤 ACTIVAR MICRÓFONO", bg="#4CAF50", fg="white", command=self.UI_activar_microfono)
        self.btn_micro.pack(fill=tk.X, padx=10, pady=15)

        self.UI_actualizar_camara()
        self.actualizar_consola(f"[Sistema]: Voces listas. Idioma natal: {self.idioma_activa}")
        self.root.mainloop()

if __name__ == "__main__":
    naic = Naic()
    naic.iniciar_interfaz_grafica()
