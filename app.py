""" from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, g, session,Response, stream_with_context
import requests
import logging
import tempfile
import os
import urllib.request

app = Flask(__name__)
#data = None
app.secret_key = 'my_very_secure_secret_key_1!'

@app.before_request
def before_request():
    print('Antes de la peticion ...')

@app.after_request
def after_request(response):
    print('Despues de la peticion ...')
    return response

@app.route('/')
def index():
    error = request.args.get('error')
    data = {
        'Titulo': 'Home',
        'bienvenida': 'YouTube Video Downloader',
        'error': error
    }
    return render_template('index.html', data = data)

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
    # Obtener los datos de la sesión
    data = session.get('data')
    
    if not data:
        return "Error: No hay datos para descargar", 400
    
    download_url = data['URL']
    video_title = data['Titulo']
    # Limpiar el título para usarlo como nombre de archivo
    video_title = "".join(x for x in video_title if x.isalnum() or x in (' ', '-', '_'))
    
    # Definir la función de flujo para transmitir el contenido del video
    def generate():
        with urllib.request.urlopen(download_url) as response:
            while True:
                chunk = response.read(1024 * 10)  # Leer en bloques de 10KB
                if not chunk:
                    break
                yield chunk

    # Crear una respuesta en flujo con el nombre de archivo adecuado
    return Response(
        stream_with_context(generate()),
        headers={
            'Content-Disposition': f'attachment; filename="{video_title}.mp4"',
            'Content-Type': 'video/mp4'
        }
    )
    

# Decorator para limpiar archivos después de la respuesta
def after_this_request(f):
    if not hasattr(g, 'after_request_callbacks'):
        g.after_request_callbacks = []
    g.after_request_callbacks.append(f)
    return f

# Modificar el after_request para incluir las callbacks
@app.after_request
def after_request(response):
    print('Despues de la peticion ...')
    for callback in getattr(g, 'after_request_callbacks', []):
        callback(response)
    return response

@app.errorhandler(404)
def page_not_found(e):
    # Redirigir a la página principal con un parámetro de error
    return redirect(url_for('index', error='route_not_found'))

if __name__ == '__main__':
    #app.run(debug=True, port=5000)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

 """

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

""" @app.route('/descarga')
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
        return f"Error de conexión al intentar descargar el video {e}", 500 """

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