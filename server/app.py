import uuid
import os
import boto3
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS, cross_origin

SONGS = []

# configuration
DEBUG = True
UPLOAD_FOLDER = 'media/songs'
ALLOWED_EXTENSIONS = set(['mp3'])
BASEDIR = os.path.abspath(os.path.dirname(__file__))
USERS_TABLE = os.environ['USERS_TABLE']
IS_OFFLINE = os.environ.get('IS_OFFLINE')

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CORS_HEADERS'] = 'Content-Type'

# setting up server for online or offline
if IS_OFFLINE:
    client = boto3.client(
        'dynamodb',
        region_name='localhost',
        endpoint_url='http://localhost:8000'
    )
else:
    client = boto3.client('dynamodb')

# enable CORS
cors = CORS(app, resources={r"/*": {"origins": "*"}}, send_wildcard=True)

# file extension checking
def allowed_filename(filename):
    return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS

# sanity check route
@app.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('new pong!')


@app.route('/songs', methods=['GET', 'POST'])
def all_songs():
    response_object = {'status': 'success'}
    if request.method == 'POST':

        # saving song file
        submitted_file = request.files.get('file')
        if submitted_file and allowed_filename(submitted_file.filename):

            name_artist = request.form.get('name') + '_' + request.form.get('artist') + '.mp3'

            file_name = secure_filename(name_artist)

            song_id = uuid.uuid4().hex
            name = request.form.get('name')
            artist = request.form.get('artist')

            # saving song data
            SONGS.append({
                'id': song_id,
                'name': name,
                'artist': artist,
                'file': file_name,
            })

            # posting song to db
            resp = client.put_item(
                TableName=USERS_TABLE
                Item = {
                    'songId': {'S': song_id},
                    'name': {'S': name},
                    'artist': {'S': artist},
                    'fileName': {'S': file_name}
                }
            )

            file_path = os.path.join(BASEDIR, app.config['UPLOAD_FOLDER'], filename)
            print("!!!")
            print(BASEDIR)
            print(filename)
            print(file_path)
            submitted_file.save(file_path)
        else:
            return jsonify({'error': 'Please provide valid file'}),400

        response_object['message'] = 'Song added!'
    else:
        # fetching songs from db
        resp = client.get_item(
            TableName = USERS_TABLE,
            Key = {
                'songId': { 'S': song_id}
            }
        )
        item = resp.get('Item')
        jsonify({})
        response_object['songs'] = SONGS
    return jsonify(response_object)


@app.route('/songs/<song_id>', methods=['GET', 'PUT', 'DELETE'])
def single_song(song_id):
    response_object = {'status': 'success'}
    if request.method == "GET":
        song = get_song(song_id)

        if song != False:
            file_path = os.path.join(BASEDIR, app.config['UPLOAD_FOLDER'], song['file'])
            
            try:
                response = send_file(file_path, 
                                     as_attachment=True,
                                     attachment_filename=song['name'] + '_' + song['artist'] + '.mp3',
                                     mimetype='audio/mpeg')
                
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Name_Artist', song['name'] + '_' + song['artist'] + '.mp3')

                return response
            
            except Exception as e:
                print("!!!")
                print(e.with_traceback)
                print("!!!")

        


    if request.method == 'PUT':
        remove_song(song_id)

        # saving song file
        submitted_file = request.files.get('file')
        if submitted_file and allowed_filename(submitted_file.filename):

            name_artist = request.form.get('name') + '_' + request.form.get('artist') + '.mp3'

            filename = secure_filename(name_artist)

            # saving song data
            SONGS.append({
                'id': uuid.uuid4().hex,
                'name': request.form.get('name'),
                'artist': request.form.get('artist'),
                'file': filename,
            })

            submitted_file.save(os.path.join(BASEDIR, app.config['UPLOAD_FOLDER'], filename))

        response_object['message'] = 'Song updated!'

    if request.method == 'DELETE':

        song = get_song(song_id)

        if song != False:
            file_path = os.path.join(BASEDIR, app.config['UPLOAD_FOLDER'], song['file'])

            try:
                os.remove(file_path)
            except Exception as e:
                print(e.with_traceback)

            remove_song(song_id)
            response_object['message'] = 'Song removed!'
        else:
            response_object['message'] = 'Song file not present to be deleted'

    return jsonify(response_object)


def get_song(song_id):
    for song in SONGS:
        if song['id'] == song_id:
            return song
    return False

def remove_song(song_id):
    for song in SONGS:
        if song['id'] == song_id:
            SONGS.remove(song)
            return True
    return False


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
