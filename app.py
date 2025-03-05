from flask import Flask, request, send_file, render_template, after_this_request
from pydub import AudioSegment
import os
import shutil
import zipfile
from datetime import datetime
import sass
import wave
import vosk
import json

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
MODEL_PATH = "models/es"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

sass.compile(dirname=('static/scss', 'static/css'), output_style='compressed')

# Sonidos predefinidos
INTRO_PATH = "static/intro.mp3"
OUTRO_PATH = "static/outro.mp3"

# Cargar el modelo de Vosk
vosk_model = vosk.Model(MODEL_PATH)

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        program_name = request.form.get("program_name", "").strip()
        transcribe = "transcribe" in request.form  # Verifica si el checkbox está marcado
        download_audio = "download_audio" in request.form  # Verifica si el otro checkbox está marcado

        if file:
            fecha = datetime.now().strftime("%y%m%d")  # Formato AAMMDD
            safe_program_name = "".join(c for c in program_name if c.isalnum() or c in " _-").strip()
            original_name, _ = os.path.splitext(file.filename)  # Extrae el nombre sin la extensión
            
            # Formato del nombre de archivo con " - "
            if safe_program_name:
                new_filename = f"{fecha} - {safe_program_name} - {original_name}.wav"
            else:
                new_filename = f"{fecha} - {original_name}.wav"

            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            output_path = os.path.join(OUTPUT_FOLDER, new_filename)
            file.save(filepath)
            
            # Cargar los audios
            intro = AudioSegment.from_file(INTRO_PATH)
            outro = AudioSegment.from_file(OUTRO_PATH)
            audio = AudioSegment.from_file(filepath)
            
            # Convertir a 44100 Hz, 16 bits, estéreo
            intro = intro.set_frame_rate(44100).set_sample_width(2).set_channels(2)
            outro = outro.set_frame_rate(44100).set_sample_width(2).set_channels(2)
            audio = audio.set_frame_rate(44100).set_sample_width(2).set_channels(2)
            
            # Concatenar audios
            final_audio = intro + audio + outro
            
            # Guardar archivo procesado en formato WAV
            final_audio.export(output_path, format="wav")

            # Si el usuario seleccionó "transcribir", generamos el texto
            text_file = None
            if transcribe:
                text_filename = os.path.splitext(output_path)[0] + ".txt"
                text_file = transcribir_audio(output_path, text_filename)

            # Si el usuario marcó ambos checkboxes, creamos un ZIP
            if transcribe and download_audio:
                # Verificar que los archivos existen
                if os.path.exists(output_path) and os.path.exists(text_file):
                    zip_filename = os.path.splitext(new_filename)[0] + ".zip"
                    zip_path = os.path.join(OUTPUT_FOLDER, zip_filename)

                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        zipf.write(output_path, os.path.basename(output_path))  # Agregar audio
                        zipf.write(text_file, os.path.basename(text_file))  # Agregar transcripción
                    
                    print(f"Archivo ZIP generado: {zip_path}")  # Depuración
                    return send_file(zip_path, as_attachment=True)
                else:
                    return "Error: No se encontraron los archivos para crear el ZIP.", 400

            # Si solo quiere descargar el audio
            elif download_audio:
                if os.path.exists(output_path):
                    return send_file(output_path, as_attachment=True)
                else:
                    return "Error: No se encontró el archivo de audio.", 400

            # Si solo quiere la transcripción
            elif transcribe:
                if os.path.exists(text_file):
                    return send_file(text_file, as_attachment=True)
                else:
                    return "Error: No se encontró el archivo de transcripción.", 400

    return render_template("index.html")

def transcribir_audio(audio_path, output_text_path):
    """Transcribe un archivo de audio usando Vosk y guarda el resultado en un archivo TXT."""
    wf = wave.open(audio_path, "rb")
    
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
        audio = AudioSegment.from_wav(audio_path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(audio_path, format="wav")

    wf = wave.open(audio_path, "rb")
    
    rec = vosk.KaldiRecognizer(vosk_model, wf.getframerate())
    rec.SetWords(True)
    transcript = ""

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            transcript += result.get("text", "") + " "

    wf.close()

    with open(output_text_path, "w", encoding="utf-8") as f:
        f.write(transcript.strip())

    return output_text_path

@app.after_request
def cleanup(response):
    """ Elimina los archivos dentro de las carpetas uploads y output después de la respuesta """
    limpiar_carpetas()
    return response

def limpiar_carpetas():
    """ Elimina los archivos dentro de las carpetas uploads y output """
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)  # Borra archivos individuales
                    print(f"Archivo borrado: {file_path}")  # Para verificar si se borran
            except Exception as e:
                print(f"Error al borrar {file_path}: {e}")

if __name__ == "__main__":
    app.run(debug=True)