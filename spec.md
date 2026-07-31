# PROMPT: Creación de Asistente de Llamadas en Tiempo Real (Copiloto IA) para macOS

Necesito desarrollar un software de escritorio para macOS que intercepte el audio de salida del sistema en tiempo real durante una llamada, lo transcriba, detecte cuando la otra persona hace una pregunta y use la API de Gemini para generar respuestas rápidas y concisas en una interfaz flotante.

---

### Pila Tecnológica Requerida
- **Sistema Operativo:** macOS (Debe soportar redirección de audio de salida).
- **Lenguaje Principal:** Python 3.10+
- **Captura de Audio:** Librería `soundcard` o `pyaudio` configurada para capturar desde el dispositivo virtual de audio (e.g., BlackHole).
- **Transcripción (STT):** `faster-whisper` (local) o `google-cloud-speech` / WebSocket de transcripción en tiempo real con baja latencia.
- **Motor de Inteligencia Artificial:** API de Google Gemini (`google-genai` SDK) usando el modelo `gemini-2.5-flash` para respuestas con ultra-baja latencia.
- **Interfaz Gráfica (GUI):** `PyQt6` o `PySide6` con soporte para ventana flotante "*Always on Top*" y fondo transparente/elegante.

---

### Arquitectura del Proyecto y Flujo de Datos

1. **Módulo de Audio (`audio_capture.py`):**
   - Escuchar continuamente el stream de entrada del dispositivo de audio configurado en el sistema (por ejemplo, BlackHole 2ch).
   - Mantener un búfer de audio continuo de bajo retardo.

2. **Módulo de Transcripción (`transcriber.py`):**
   - Procesar los bloques de audio del búfer y convertirlos a texto en tiempo real.
   - Detectar pauses/silencios para determinar cuándo se completó una frase o pregunta.

3. **Módulo de IA con Gemini (`ai_assistant.py`):**
   - Recibir el texto transcrito.
   - Utilizar la API de Gemini para evaluar si el texto corresponde a una pregunta o solicitud.
   - Configurar el prompt del sistema (*System Instruction*) para Gemini:
     > *"Eres un copiloto de entrevistas y llamadas en tiempo real. Tu trabajo es dar respuestas directas, profesionales, breves y formateadas en viñetas (bullet points) para que el usuario pueda leerlas de un vistazo rápido durante la llamada. Evita introducciones innecesarias."*
   - Retornar la respuesta generada por Gemini a la interfaz gráfica.

4. **Interfaz Gráfica (`gui.py`):**
   - Ventana flotante pequeña, estilizada en modo oscuro o translúcida.
   - Mantiene la propiedad `Qt.WindowStaysOnTopHint`.
   - Muestra dos secciones principales:
     1. **Transcripción en vivo** (Lo que el interlocutor está diciendo).
     2. **Sugerencias de Gemini** (Puntos clave de respuesta).
   - Incluye un botón para limpiar el historial y un indicador visual de nivel de audio/micrófono.

---

### Instrucciones de Estructura de Código

Por favor, genera la estructura completa del proyecto con los siguientes archivos:
1. `requirements.txt` (Con todas las librerías necesarias).
2. `README.md` (Instrucciones paso a paso para instalar BlackHole en macOS y configurar el audio multisalida en la app 'Configuración de Audio MIDI').
3. `config.py` (Manejo de variables de entorno como `GEMINI_API_KEY` y parámetros de audio).
4. `src/audio_capture.py`
5. `src/transcriber.py`
6. `src/ai_assistant.py`
7. `src/gui.py`
8. `main.py` (Punto de entrada de la aplicación).

Asegúrate de incluir manejo de errores adecuado para dispositivos de audio no encontrados y claves de API faltantes.