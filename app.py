from flask import Flask, render_template, request, redirect, url_for, session, Response, stream_with_context, abort
import requests
import logging
import os
import urllib.request
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_very_secure_secret_key_1!'
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    error = request.args.get('error')
    data = {
        'Titulo': 'YouTube Video Downloader',
        'bienvenida': 'YouTube Video Downloader',
        'error': error
    }
    return render_template('index.html', data=data)

@app.route('/search_video')
def search_video():
    try:
        video_url = request.args.get('url')
        if not video_url:
            return redirect(url_for('index', error='Por favor ingrese una URL'))

        if 'youtube.com' not in video_url and 'youtu.be' not in video_url:
            return redirect(url_for('index', error='URL inválida. Por favor ingrese una URL de YouTube'))

        # Extraer el ID del video
        video_id = None
        if 'v=' in video_url:
            video_id = video_url.split('v=')[1].split('&')[0]
        elif 'youtu.be' in video_url:
            video_id = video_url.split('/')[-1].split('?')[0]

        if not video_id:
            return redirect(url_for('index', error='No se pudo obtener el ID del video'))

        # Llamada a la API
        api_url = "https://yt-api.p.rapidapi.com/dl"
        querystring = {"id": video_id}
        headers = {
            "x-rapidapi-key": "72ea23ea89mshf6775ef3b0dde3cp1c8da5jsn0d645a94c48c",
            "x-rapidapi-host": "yt-api.p.rapidapi.com"
        }

        response = requests.get(api_url, headers=headers, params=querystring)
        data = response.json()

        if 'formats' not in data:
            return redirect(url_for('index', error='No se pudo obtener la información del video'))

        # Preparar datos para la plantilla
        data_to_html = {
            'Titulo': data.get('title', 'Video sin título'),
            'Image_url': data.get('thumbnail', [{}] * 5)[4].get('url', '')
        }

        # Guardar información para la descarga
        session['download_info'] = {
            'title': data.get('title', 'video'),
            'url': data.get('formats', [{}])[0].get('url', '')
        }

        return render_template('video_found.html', data=data_to_html)

    except Exception as e:
        logger.error(f"Error en search_video: {str(e)}")
        return redirect(url_for('index', error='Error al procesar el video'))

@app.route('/descarga')
def descarga():
    try:
        download_info = session.get('download_info')
        if not download_info or 'url' not in download_info:
            return redirect(url_for('index', error='No hay información de descarga disponible'))

        def generate():
            try:
                with urllib.request.urlopen(download_info['url']) as response:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        yield chunk
            except Exception as e:
                logger.error(f"Error during download: {str(e)}")
                abort(500)

        # Sanitizar el nombre del archivo
        filename = "".join(x for x in download_info['title'] if x.isalnum() or x in (' ', '-', '_'))
        filename = f"{filename[:100]}.mp4"  # Limitar longitud del nombre

        return Response(
            stream_with_context(generate()),
            headers={
                'Content-Type': 'video/mp4',
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        logger.error(f"Error en descarga: {str(e)}")
        return redirect(url_for('index', error='Error al iniciar la descarga'))

@app.errorhandler(404)
def not_found_error(error):
    return redirect(url_for('index', error='Página no encontrada'))

@app.errorhandler(500)
def internal_error(error):
    return redirect(url_for('index', error='Error interno del servidor'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)