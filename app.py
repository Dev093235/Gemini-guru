# app.py file (Updated for searching on archive.org)

from flask import Flask, request, send_file, jsonify
import os
import yt_dlp
import tempfile

app = Flask(__name__)

# Default route for the server
@app.route('/')
def home():
    return "Hello! This is a simple audio downloader server for your college practical. Use the /download?query=<song_name> route to search and download an audio file from archive.org."

# Route to search and download the audio by name from archive.org
@app.route('/download', methods=['GET'])
def search_and_download_audio():
    search_query = request.args.get('query')

    if not search_query:
        return jsonify({"error": "Kripya 'query' parameter provide karein (gaane ka naam)."}), 400

    # Yahan hum 'archive.org:search:' prefix use kar rahe hain
    # Isse yt-dlp archive.org par search karega aur pehla result lega
    yt_dlp_query = f"archive.org:search:{search_query}" # Yahan badlav kiya gaya hai

    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = os.path.join(tmpdir, '%(title)s.%(ext)s')

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': output_template,
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'external_downloader_args': ['-user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36'],
            'extractor_retries': 'auto',
            # 'default_search': 'ytsearch', # Ab iski zaroorat nahi, hum explicitly archive.org search kar rahe hain
            'no_warnings': True,
            'quiet': True,
            'skip_download': False
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(yt_dlp_query, download=True)
                filename_without_ext = ydl.prepare_filename(info)

                mp3_filepath = None
                for file in os.listdir(tmpdir):
                    if file.startswith(os.path.basename(filename_without_ext)) and file.endswith('.mp3'):
                        mp3_filepath = os.path.join(tmpdir, file)
                        break

                if not mp3_filepath or not os.path.exists(mp3_filepath):
                    downloaded_files = [f for f in os.listdir(tmpdir) if os.path.isfile(os.path.join(tmpdir, f))]
                    audio_file = None
                    for f in downloaded_files:
                        if f.endswith(('.mp3', '.m4a', '.webm', '.ogg')):
                            audio_file = os.path.join(tmpdir, f)
                            break
                    if audio_file:
                         return send_file(audio_file, as_attachment=True, mimetype='audio/mpeg')
                    else:
                         return jsonify({"error": "Gaana download nahi ho paya ya MP3 file nahi mili."}), 500

                return send_file(mp3_filepath, as_attachment=True, mimetype='audio/mpeg')

        except Exception as e:
            print(f"Error during download: {e}")
            return jsonify({"error": f"Gaana download karte waqt error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
