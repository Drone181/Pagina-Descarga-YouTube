from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, g, session
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
    cursos = {'PHP', 'Python', 'Java', 'Kotlin', 'Dart', 'JavaScript'}
    data = {
        'Titulo': 'Index',
        'bienvenida': 'Saludos!',
        'cursos': cursos,
        'numero_cursos': len(cursos)
    }
    return render_template('index.html', data = data)

@app.route('/search_video', methods=['GET'])
def search_video():
    #global data

    str = request.args.get('url')
    str = str[32:]
    
    url = "https://yt-api.p.rapidapi.com/dl"
    querystring = {"id":str,"cgeo":"DE"}
    headers = {
        "x-rapidapi-key": "72ea23ea89mshf6775ef3b0dde3cp1c8da5jsn0d645a94c48c",
        "x-rapidapi-host": "yt-api.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
 
    if 'formats' in data:

        data_to_html = {
            'Titulo': data.get('title','video'),
            'Image_url': data.get('thumbnail','no tm')[4]['url']
        }

        download_info = {
            'Titulo': data.get('title','video'),
            'URL': data.get('formats','no data')[0]['url']
        }

        # Guardamos los datos de la API en la sesión
        session['data'] = download_info
        #return data.get('formats','no formats')
        return render_template('video_found.html', data = data_to_html)

    return 'Video url not valid'
    
@app.route('/descarga')
def descarga():
    #global data
    data = session.get('data')

    if not data:
        return "Error: No hay datos para descargar", 400
    
    download_url = data['URL']
    
    # Obtener el título del video para usarlo como nombre del archivo
    video_title = data['Titulo']
    # Limpiar el título para usarlo como nombre de archivo
    video_title = "".join(x for x in video_title if x.isalnum() or x in (' ','-','_'))
    
    # Crear un archivo temporal
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"{video_title}.mp4")
    
    # Descargar el archivo
    urllib.request.urlretrieve(download_url, temp_path)
    
    # Enviar el archivo al cliente y eliminar el temporal después
    try:
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=f"{video_title}.mp4",
            mimetype='video/mp4'
        )
    finally:
        # Programar la eliminación del archivo temporal
        @after_this_request
        def remove_file(response):
            try:
                os.remove(temp_path)
            except Exception as error:
                app.logger.error("Error removing downloaded file", error)
            return response
    
    

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


if __name__ == '__main__':
    app.run(debug=True, port=5000)

