# app.py file

from flask import Flask, request, send_file, jsonify
import os
import yt_dlp
import tempfile

app = Flask(__name__)

# Default route for the server
@app.route('/')
def home():
    return "Hello! This is a simple audio downloader server for your college practical. Use the /download route to get an audio file."

# Route to download the audio
@app.route('/download', methods=['GET'])
def download_audio():
    # Get the URL from the request parameters (e.g., /download?url=YOUR_VIDEO_URL)
    video_url = request.args.get('url')

    if not video_url:
        return jsonify({"error": "Please provide a 'url' parameter in the request."}), 400

    # Create a temporary directory to store the downloaded file
    # This is crucial for platforms like Render, where the file system is temporary.
    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = os.path.join(tmpdir, '%(title)s.%(ext)s')

        # yt-dlp options to download best audio and convert to MP3
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192', # Audio quality in kbps
            }],
            'outtmpl': output_template,
            'restrictfilenames': True, # Keep filenames web-friendly
            'noplaylist': True,        # Download single video, not a playlist
            'nocheckcertificate': True, # Sometimes needed for HTTPS
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                filename_without_ext = ydl.prepare_filename(info)

                # Find the exact MP3 file path within the temporary directory
                mp3_filepath = None
                for file in os.listdir(tmpdir):
                    if file.startswith(os.path.basename(filename_without_ext)) and file.endswith('.mp3'):
                        mp3_filepath = os.path.join(tmpdir, file)
                        break

                if not mp3_filepath or not os.path.exists(mp3_filepath):
                    # Fallback: if MP3 not found, try to send any downloaded audio file
                    downloaded_files = [f for f in os.listdir(tmpdir) if os.path.isfile(os.path.join(tmpdir, f))]
                    audio_file = None
                    for f in downloaded_files:
                        if f.endswith(('.mp3', '.m4a', '.webm', '.ogg')): # Check for common audio formats
                            audio_file = os.path.join(tmpdir, f)
                            break
                    if audio_file:
                         return send_file(audio_file, as_attachment=True, mimetype='audio/mpeg')
                    else:
                         return jsonify({"error": "Failed to download or find suitable audio file."}), 500

            # Send the downloaded MP3 file to the user
                return send_file(mp3_filepath, as_attachment=True, mimetype='audio/mpeg')

        except Exception as e:
            # Log the error for debugging (Render will show this in logs)
            print(f"Error during download: {e}")
            return jsonify({"error": f"An error occurred during download: {str(e)}"}), 500

# This ensures the server runs when the script is executed
if __name__ == '__main__':
    # Use PORT environment variable if available (for Render), otherwise default to 5000
    port = int(os.environ.get("PORT", 5000))
    # host='0.0.0.0' allows the server to be accessible from outside the local machine
    app.run(debug=False, host='0.0.0.0', port=port) # Set debug to False for production/deployment
