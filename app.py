from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, g, session,Response, stream_with_context
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

""" @app.route('/search_video', methods=['GET'])
def search_video():
    #global data

    str = request.args.get('url')

    if "v=" in str:
        str = str.split("v=")[1].split("&")[0]
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
    else:

        return 'Video url not valid' """

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
   
""" @app.route('/descarga')
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
            return response """
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

