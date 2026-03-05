from flask import Flask, request, send_file
import yt_dlp
import whisper
from gtts import gTTS
from deep_translator import GoogleTranslator
import os

app = Flask(__name__)


# 🔽 Download audio from YouTube
def download_audio(url):

    # Remove old files
    if os.path.exists("audio.wav"):
        os.remove("audio.wav")

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": "audio.%(ext)s",
        "noplaylist": True,
        "quiet": False,

        # Android client trick (avoids bot detection sometimes)
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        },

        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "192",
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Audio Translator</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f5f5f5;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }

            .card {
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.08);
                width: 400px;
            }

            h2 {
                margin-top: 0;
                text-align: center;
            }

            input, select, button {
                width: 100%;
                padding: 12px;
                margin-top: 15px;
                border-radius: 8px;
                border: 1px solid #ddd;
                font-size: 14px;
            }

            button {
                background: black;
                color: white;
                border: none;
                cursor: pointer;
                font-weight: bold;
            }

            button:hover {
                opacity: 0.9;
            }

            .small {
                text-align: center;
                font-size: 12px;
                margin-top: 15px;
                color: gray;
            }
        </style>
    </head>

    <body>

        <div class="card">

            <h2>🎧 AI Audio Translator</h2>

            <form method="POST" action="/dub">

                <input name="url" placeholder="Paste YouTube link" required />

                <select name="language">
                    <option value="hi">Hindi</option>
                    <option value="ta">Tamil</option>
                    <option value="te">Telugu</option>
                    <option value="ur">Urdu</option>
                    <option value="fr">French</option>
                    <option value="es">Spanish</option>
                    <option value="de">German</option>
                </select>

                <button type="submit" id="btn">
                    Translate Audio
                </button>

            </form>

            <div class="small">
                Works best with short videos
            </div>

        </div>

        <script>

            const form = document.querySelector("form")
            const btn = document.getElementById("btn")

            form.addEventListener("submit", function(){

                btn.innerText = "Processing... Please wait"
                btn.disabled = true

            })

        </script>

    </body>

    </html>
    """


@app.route("/dub", methods=["POST"])
def dub():

    try:

        url = request.form["url"]
        target_lang = request.form["language"]

        # 1️⃣ Download audio
        download_audio(url)

        if not os.path.exists("audio.wav"):
            return "Error: audio.wav not created."

        # 2️⃣ Whisper transcription
        model = whisper.load_model("tiny")
        result = model.transcribe("audio.wav", task="translate", fp16=False)
        english_text = result["text"]

        # 3️⃣ Translate
        translated_text = GoogleTranslator(
            source="auto",
            target=target_lang
        ).translate(english_text)

        # 4️⃣ Generate speech
        tts = gTTS(text=translated_text, lang=target_lang)
        tts.save("output.mp3")

        response = send_file("output.mp3", as_attachment=True)

        # Cleanup
        if os.path.exists("audio.wav"):
            os.remove("audio.wav")

        if os.path.exists("output.mp3"):
            os.remove("output.mp3")

        return response

    except Exception as e:
        return f"<h3>Error occurred:</h3><pre>{str(e)}</pre>"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)