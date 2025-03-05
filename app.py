from flask import Flask, request, send_file, render_template, after_this_request
from pydub import AudioSegment
import os
import shutil
from datetime import datetime
import sass

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

sass.compile(dirname=('static/scss', 'static/css'), output_style='compressed')

# Sonidos predefinidos
INTRO_PATH = "static/intro.mp3"
OUTRO_PATH = "static/outro.mp3"

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        program_name = request.form.get("program_name", "").strip()
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

            # Enviar archivo al usuario
            return send_file(output_path, as_attachment=True)

    return render_template("index.html")

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
