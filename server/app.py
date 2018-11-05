import uuid
import os
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request
from flask_cors import CORS

SONGS = []

# configuration
DEBUG = True
UPLOAD_FOLDER = '/media/songs'
ALLOWED_EXTENSIONS = set(['mp3'])

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# enable CORS
CORS(app)

#File extension checking
def allowed_filename(filename):
    return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS

# sanity check route
@app.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('pong!')


@app.route('/songs', methods=['GET', 'POST'])
def all_songs():
    response_object = {'status': 'success'}
    if request.method == 'POST':

        # saving song data
        SONGS.append({
            'id': uuid.uuid4().hex,
            'name': request.form.get('name'),
            'artist': request.form.get('artist'),
            'listened': request.form.get('listened')
        })

        # saving song file
        submitted_file = request.files.get('file')
        if submitted_file and allowed_filename(submitted_file.filename):
            filename = secure_filename(submitted_file.filename)
            submitted_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        response_object['message'] = 'Song added!'
    else:
        response_object['songs'] = SONGS
    return jsonify(response_object)


@app.route('/songs/<song_id>', methods=['PUT', 'DELETE'])
def single_song(song_id):
    response_object = {'status': 'success'}
    if request.method == 'PUT':
        post_data = request.get_json()
        remove_song(song_id)

        # adding song data to array
        SONGS.append({
            'id': uuid.uuid4().hex,
            'name': post_data.get('name'),
            'artist': post_data.get('artist'),
            'listened': post_data.get('listened')
        })

        # saving song file
        submitted_file = request.files['file']
        if submitted_file and allowed_filename(submitted_file.filename):
            filename = secure_filename(submitted_file.filename)
            submitted_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))


        response_object['message'] = 'Song updated!'
    if request.method == 'DELETE':
        remove_song(song_id)
        response_object['message'] = 'Song removed!'
    return jsonify(response_object)


def remove_song(song_id):
    for song in SONGS:
        if song['id'] == song_id:
            SONGS.remove(song)
            return True
    return False


if __name__ == '__main__':
    app.run()
