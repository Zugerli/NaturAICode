# motor_naic_v0.2.py
import pyttsx3

class Naic:
    def __init__(self):
        self.engine_voz = pyttsx3.init()
        self.nombre_agente = "Naic"

    def ejecutar(self, comando):
        comando = comando.strip().lower()

        if "voz.decir" in comando:
            texto = comando.split('"')[1]
            print(f"[{self.nombre_agente}]: {texto}")
            self.engine_voz.say(texto)
            self.engine_voz.runAndWait()

        elif "cerebro.razonar" in comando:
            pregunta = comando.split('"')[1]
            print(f"[Cerebro]: Analizando '{pregunta}'...")
            # Aquí simulamos la respuesta, en el futuro conectará con el LLM
            respuesta = "He analizado tu petición y los datos son correctos. Procediendo."
            print(f"[Respuesta]: {respuesta}")
            self.engine_voz.say(respuesta)
            self.engine_voz.runAndWait()

        elif "crear_interfaz" in comando:
            print("[Naic]: Generando ventana de control visual...")
            print("-----------------------------------")
            print("|  [ BOTÓN A ]    [ BOTÓN B ]     |")
            print("-----------------------------------")

    def probar(self, codigo_naic):
        lineas = codigo_naic.split('\n')
        for linea in lineas:
            if linea.strip() and not linea.startswith("//"):
                self.ejecutar(linea)

# PRUEBA DE USUARIO (Zugerli)
mi_app = """
voz.decir("Iniciando sistema Naic-AI")
cerebro.razonar("¿Estás listo para ayudar a los estudiantes?")
crear_interfaz("botones")
"""

naic_instancia = Naic()
naic_instancia.probar(mi_app)