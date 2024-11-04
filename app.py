""" from flask import Flask, render_template, request, redirect, url_for, jsonify, session, Response, stream_with_context
import requests
import logging
import os
import re
import urllib.request
from urllib.error import HTTPError
import datetime

app = Flask(__name__)
app.secret_key = 'my_very_secure_secret_key_1!'
logging.basicConfig(level=logging.INFO)

@app.before_request
def before_request():
    logging.info('Before request...')

@app.after_request
def after_request(response):
    logging.info('After request...')
    return response

@app.route('/')
def index():
    error = request.args.get('error')
    data = {
        'Titulo': 'Home',
        'bienvenida': 'YouTube Video Downloader',
        'error': error
    }
    return render_template('index.html', data=data)

@app.route('/search_video', methods=['GET'])
def search_video():
    str = request.args.get('url')

    if not str:
        #return jsonify({'error': 'Por favor ingrese una URL de YouTube'}), 400
        return redirect(url_for('index'))

    if "v=" not in str:
        return jsonify({'error': 'URL de video no válida'}), 400

    try:
        str = str.split("v=")[1].split("&")[0]
        url = "https://yt-api.p.rapidapi.com/dl"
        querystring = {"id":str,"cgeo":"DE"}
        headers = {
            "x-rapidapi-key": "72ea23ea89mshf6775ef3b0dde3cp1c8da5jsn0d645a94c48c",
            "x-rapidapi-host": "yt-api.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()

        if 'formats' not in data:
            return jsonify({'error': 'No se pudo obtener la información del video'}), 400

        data_to_html = {
            'Titulo': data.get('title','video'),
            'Image_url': data.get('thumbnail','no tm')[4]['url']
        }

        download_info = {
            'Titulo': data.get('title','video'),
            'URL': data.get('formats','no data')[0]['url']
        }

        session['data'] = download_info
        return render_template('video_found.html', data=data_to_html)

    except Exception as e:
        return jsonify({'error': 'Ocurrió un error al procesar el video'}), 400

@app.route('/descarga')
def descarga():
    download_info = session.get('data')
    
    if not download_info:
        return redirect(url_for('index', error='No hay información de descarga disponible'))
    
    video_url = download_info['URL']
    video_title = download_info['Titulo']

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'
        }
        response = requests.get(video_url, headers=headers, stream=True)
        
        if response.status_code == 200:
            return Response(
                response.iter_content(chunk_size=1024),
                content_type=response.headers.get('Content-type', 'application/octet-stream'),
                headers={
                    'Content-Disposition': f'attachment; filename="{video_title}.mp4"'
                }
            )
        else:
            return f"Error al descargar el video: Código de estado {response.status_code}", 500
    except requests.RequestException as e:
        return f"Error de conexión al intentar descargar el video {e}", 500

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('index', error='Página no encontrada'))

@app.errorhandler(500)
def server_error(e):
    return redirect(url_for('index', error='Error interno del servidor'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) """

from flask import Flask, render_template, request, redirect, url_for, jsonify, session, Response
import requests
import logging
import os
import time
from urllib.parse import quote
from requests.exceptions import RequestException
from werkzeug.contrib.fixers import ProxyFix  # Para manejar correctamente las cabeceras en Render

app = Flask(__name__)
app.secret_key = 'my_very_secure_secret_key_1!'
# Configuración de sesión más robusta
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutos
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configuración de logging más detallada
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Aplicar ProxyFix para manejar correctamente las cabeceras en Render
app.wsgi_app = ProxyFix(app.wsgi_app)

@app.route('/search_video', methods=['GET'])
def search_video():
    video_url = request.args.get('url')
    
    if not video_url:
        logger.warning("No URL provided")
        return redirect(url_for('index'))

    if "v=" not in video_url:
        logger.warning("Invalid YouTube URL format")
        return redirect(url_for('index', error='URL de video no válida'))

    try:
        video_id = video_url.split("v=")[1].split("&")[0]
        api_url = "https://yt-api.p.rapidapi.com/dl"
        querystring = {"id": video_id, "cgeo": "DE"}
        headers = {
            "x-rapidapi-key": "72ea23ea89mshf6775ef3b0dde3cp1c8da5jsn0d645a94c48c",
            "x-rapidapi-host": "yt-api.p.rapidapi.com"
        }

        logger.info(f"Fetching video info for ID: {video_id}")
        response = requests.get(api_url, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'formats' not in data:
            logger.error("No formats found in API response")
            return redirect(url_for('index', error='No se pudo obtener la información del video'))

        # Guardar información en sesión
        download_info = {
            'Titulo': data.get('title', 'video'),
            'URL': data.get('formats', [])[0]['url'],
            'timestamp': time.time()  # Para verificar la frescura de los datos
        }
        session['data'] = download_info
        logger.info("Video info successfully stored in session")

        data_to_html = {
            'Titulo': download_info['Titulo'],
            'Image_url': data.get('thumbnail', [])[4]['url'] if len(data.get('thumbnail', [])) > 4 else None
        }

        return render_template('video_found.html', data=data_to_html)

    except Exception as e:
        logger.error(f"Error in search_video: {str(e)}", exc_info=True)
        return redirect(url_for('index', error='Error al procesar el video'))

@app.route('/descarga')
def descarga():
    try:
        # Verificar si hay datos en la sesión
        download_info = session.get('data')
        if not download_info:
            logger.error("No download information found in session")
            return redirect(url_for('index', error='No hay información de descarga disponible'))

        # Verificar la frescura de los datos
        if time.time() - download_info.get('timestamp', 0) > 1800:  # 30 minutos
            logger.warning("Session data has expired")
            return redirect(url_for('index', error='La sesión ha expirado, por favor busque el video nuevamente'))

        video_url = download_info['URL']
        video_title = download_info['Titulo']
        
        # Sanitizar el nombre del archivo
        video_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_'))[:100]
        safe_filename = quote(video_title + '.mp4')

        logger.info(f"Starting download for video: {safe_filename}")

        # Headers para la solicitud
        request_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'identity;q=1, *;q=0',
            'Connection': 'keep-alive',
            'Range': 'bytes=0-'
        }

        # Verificar disponibilidad del video antes de iniciar la descarga
        head_response = requests.head(video_url, headers=request_headers, timeout=5)
        head_response.raise_for_status()

        def generate():
            with requests.get(video_url, headers=request_headers, stream=True, timeout=30) as response:
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk

        response_headers = {
            'Content-Disposition': f'attachment; filename="{safe_filename}"',
            'Content-Type': 'video/mp4',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }

        # Si el servidor proporciona el tamaño del contenido, añadirlo
        if 'content-length' in head_response.headers:
            response_headers['Content-Length'] = head_response.headers['content-length']

        logger.info("Starting streaming response")
        return Response(
            generate(),
            headers=response_headers,
            direct_passthrough=True
        )

    except RequestException as e:
        logger.error(f"Request error during download: {str(e)}", exc_info=True)
        return redirect(url_for('index', error='Error al descargar el video. Por favor, intente nuevamente.'))
    except Exception as e:
        logger.error(f"Unexpected error during download: {str(e)}", exc_info=True)
        return redirect(url_for('index', error='Error inesperado durante la descarga'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)