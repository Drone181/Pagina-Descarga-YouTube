from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, g, session, Response, stream_with_context
import requests
import logging
import os
import urllib.request
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = 'my_very_secure_secret_key_1!'

# Configurar para trabajar detrás de proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.before_request
def before_request():
    logger.info('Antes de la peticion ...')

@app.after_request
def after_request(response):
    logger.info('Despues de la peticion ...')
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
    try:
        str_url = request.args.get('url')

        if not str_url:
            return redirect(url_for('index', error='Por favor ingrese una URL de YouTube'))

        if "v=" not in str_url:
            return redirect(url_for('index', error='URL de video no válida'))

        video_id = str_url.split("v=")[1].split("&")[0]
        url = "https://yt-api.p.rapidapi.com/dl"
        querystring = {"id": video_id, "cgeo": "DE"}
        headers = {
            "x-rapidapi-key": "72ea23ea89mshf6775ef3b0dde3cp1c8da5jsn0d645a94c48c",
            "x-rapidapi-host": "yt-api.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()

        if 'formats' not in data:
            return redirect(url_for('index', error='No se pudo obtener la información del video'))

        data_to_html = {
            'Titulo': data.get('title', 'video'),
            'Image_url': data.get('thumbnail', [])[4]['url'] if len(data.get('thumbnail', [])) > 4 else ''
        }

        download_info = {
            'Titulo': data.get('title', 'video'),
            'URL': data.get('formats', [])[0]['url'] if data.get('formats') else ''
        }

        session['data'] = download_info
        return render_template('video_found.html', data=data_to_html)

    except Exception as e:
        logger.error(f"Error en search_video: {str(e)}")
        return redirect(url_for('index', error='Ocurrió un error al procesar el video'))

@app.route('/descarga')
def descarga():
    try:
        data = session.get('data')
        
        if not data:
            return "Error: No hay datos para descargar", 400
        
        download_url = data['URL']
        video_title = data['Titulo']
        video_title = "".join(x for x in video_title if x.isalnum() or x in (' ', '-', '_'))
        
        def generate():
            with urllib.request.urlopen(download_url) as response:
                while True:
                    chunk = response.read(1024 * 10)
                    if not chunk:
                        break
                    yield chunk

        return Response(
            stream_with_context(generate()),
            headers={
                'Content-Disposition': f'attachment; filename="{video_title}.mp4"',
                'Content-Type': 'video/mp4'
            }
        )
    except Exception as e:
        logger.error(f"Error en descarga: {str(e)}")
        return redirect(url_for('index', error='Error al descargar el video'))

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('index', error='Página no encontrada'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)