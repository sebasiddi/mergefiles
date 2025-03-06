from flask import Flask, request, send_file, render_template
from pydub import AudioSegment
import os
import zipfile
from datetime import datetime
import sass
import wave
import vosk
import json
import yt_dlp

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
MODEL_PATH = "models/es"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

sass.compile(dirname=('static/scss', 'static/css'), output_style='compressed')

INTRO_PATH = "static/intro.mp3"
OUTRO_PATH = "static/outro.mp3"

vosk_model = vosk.Model(MODEL_PATH)

def download_twitter_audio(url):
    options = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(UPLOAD_FOLDER, 'twitter_audio.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])
    for file in os.listdir(UPLOAD_FOLDER):
        if file.startswith("twitter_audio") and file.endswith(".mp3"):
            return os.path.join(UPLOAD_FOLDER, file)
    return None

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files.get("file")
        twitter_url = request.form.get("twitter_url", "").strip()
        program_name = request.form.get("program_name", "").strip()
        transcribe = "transcribe" in request.form
        download_audio = "download_audio" in request.form
        enable_trim = "enable_trim" in request.form
        start_time = request.form.get("start_time", "0").strip()
        end_time = request.form.get("end_time", "").strip()

        if not file and not twitter_url:
            return "Error: Debes subir un archivo o ingresar un enlace de Twitter.", 400

        if twitter_url:
            filepath = download_twitter_audio(twitter_url)
            if not filepath:
                return "Error: No se pudo descargar el audio de Twitter.", 400
        else:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

        fecha = datetime.now().strftime("%y%m%d")
        safe_program_name = "".join(c for c in program_name if c.isalnum() or c in " _-").strip()
        original_name, _ = os.path.splitext(os.path.basename(filepath))
        new_filename = f"{fecha} - {safe_program_name} - {original_name}.wav" if safe_program_name else f"{fecha} - {original_name}.wav"
        output_path = os.path.join(OUTPUT_FOLDER, new_filename)

        intro = AudioSegment.from_file(INTRO_PATH)
        outro = AudioSegment.from_file(OUTRO_PATH)
        audio = AudioSegment.from_file(filepath)
        
        if enable_trim and start_time.isdigit() and end_time.isdigit():
            start_ms = int(start_time) * 1000
            end_ms = int(end_time) * 1000 if end_time else len(audio)
            audio = audio[start_ms:end_ms]

        intro = intro.set_frame_rate(44100).set_sample_width(2).set_channels(2)
        outro = outro.set_frame_rate(44100).set_sample_width(2).set_channels(2)
        audio = audio.set_frame_rate(44100).set_sample_width(2).set_channels(2)

        final_audio = intro + audio + outro
        final_audio.export(output_path, format="wav")

        text_file = None
        if transcribe:
            text_filename = os.path.splitext(output_path)[0] + ".txt"
            text_file = transcribir_audio(output_path, text_filename)

        if transcribe and download_audio:
            if os.path.exists(output_path) and os.path.exists(text_file):
                zip_filename = os.path.splitext(new_filename)[0] + ".zip"
                zip_path = os.path.join(OUTPUT_FOLDER, zip_filename)
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    zipf.write(output_path, os.path.basename(output_path))
                    zipf.write(text_file, os.path.basename(text_file))
                return send_file(zip_path, as_attachment=True)
            return "Error: No se encontraron los archivos para crear el ZIP.", 400

        elif download_audio:
            if os.path.exists(output_path):
                return send_file(output_path, as_attachment=True)
            return "Error: No se encontró el archivo de audio.", 400

        elif transcribe:
            if os.path.exists(text_file):
                return send_file(text_file, as_attachment=True)
            return "Error: No se encontró el archivo de transcripción.", 400

    return render_template("index.html")

def transcribir_audio(audio_path, output_text_path):
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

if __name__ == "__main__":
    app.run(debug=True)
