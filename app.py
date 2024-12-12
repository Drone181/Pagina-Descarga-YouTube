from flask import Flask, render_template, request, redirect, url_for, jsonify, session, Response, stream_with_context
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

def obtener_codigo_video(url): 
    # Definir patrones para diferentes formatos de enlaces 
    patrones = [ 
         r'youtu\.be/([^?&]+)', # Formato: https://youtu.be/VIDEO_ID 
         r'youtube\.com/watch\?v=([^&]+)', # Formato: https://www.youtube.com/watch?v=VIDEO_ID 
         r'youtube\.com/shorts/([^?&]+)' # Formato: https://www.youtube.com/shorts/VIDEO_ID 
    ]
    
    for patron in patrones: 
        coincidencia = re.search(patron, url) 
        if coincidencia: 
         return coincidencia.group(1)
    
    return 0

@app.route('/search_video', methods=['GET'])
def search_video():
    str = request.args.get('url')

    if not str:
        #return jsonify({'error': 'Por favor ingrese una URL de YouTube'}), 400
        return redirect(url_for('index'))

    str = obtener_codigo_video(str)
    if str == 0:
        return jsonify({'error': 'URL de video no válida'}), 400

    try:
        # str = str.split("v=")[1].split("&")[0]
        
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
            'Image_url': data.get('thumbnail','no tm')[4]['url'],
            'Video_url': data.get('formats','no data')[0]['url']
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
            'Referer': 'https://www.youtube.com/'
        }
        response = requests.get(video_url, headers=headers, stream=True)

        # Verificar que la URL es accesible antes de iniciar la descarga
        head_response = requests.head(video_url, headers=headers)
        if head_response.status_code != 200:
            return redirect(url_for('index', error='El video no está accesible desde el servidor'))

        
        
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
        return f"Error de conexión al intentar descargar el video: {e}", 500


@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('index', error='Página no encontrada'))

@app.errorhandler(500)
def server_error(e):
    return redirect(url_for('index', error='Error interno del servidor'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)