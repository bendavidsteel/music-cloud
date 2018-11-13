import uuid
import os
import boto3
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS, cross_origin

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

            # posting song to db
            resp = client.put_item(
                TableName=USERS_TABLE,
                Item = {
                    'songId': {'S': song_id},
                    'name': {'S': name},
                    'artist': {'S': artist},
                    'fileName': {'S': file_name}
                }
            )

            file_path = os.path.join(BASEDIR, app.config['UPLOAD_FOLDER'], file_name)
            submitted_file.save(file_path)
        else:
            return jsonify({'error': 'Please provide valid file'}),400

        response_object['message'] = 'Song added!'
    
    if request.method == 'GET':
        # fetching songs from db
        resp = client.scan(
            TableName = USERS_TABLE
        )

        items = resp.get('Items')

        SONGS = []

        for item in items:
            SONGS.append({
                'id': item.get('songId').get('S'),
                'name': item.get('name').get('S'),
                'artist': item.get('artist').get('S')
            })

        response_object['songs'] = SONGS
    return jsonify(response_object)


@app.route('/songs/<song_id>', methods=['GET', 'PUT', 'DELETE'])
def single_song(song_id):
    response_object = {'status': 'success'}
    if request.method == "GET":

        resp = client.get_item(
            TableName = USERS_TABLE,
            Key = {
                'songId': {'S':song_id }
            }
        )
        item = resp.get('Item')

        if not item:
            return jsonify({'error': 'Song does not exist'}), 404

        file_name = item.get('fileName').get('S')

        file_path = os.path.join(BASEDIR, app.config['UPLOAD_FOLDER'], file_name)
        
        try:
            response = send_file(file_path, 
                                    as_attachment=True,
                                    mimetype='audio/mpeg')
            
            response.headers.add('Access-Control-Allow-Origin', '*')

            return response
        
        except Exception as e:
            print(e.with_traceback)
            return jsonify({'error': 'Unable to deliver song file'}), 400

        


    if request.method == 'PUT':

        # saving song file
        submitted_file = request.files.get('file')
        if submitted_file and allowed_filename(submitted_file.filename):

            name_artist = request.form.get('name') + '_' + request.form.get('artist') + '.mp3'

            file_name = secure_filename(name_artist)

            name = request.form.get('name')
            artist = request.form.get('artist')

            print(name)

            # posting song to db
            resp = client.update_item(
                TableName=USERS_TABLE,
                Key = {
                    'songId': {'S': song_id},
                    'name': {'S': name},
                    'artist': {'S': artist},
                    'fileName': {'S': file_name}
                }
            )

            submitted_file.save(os.path.join(BASEDIR, app.config['UPLOAD_FOLDER'], file_name))
        else:
            name = request.form.get('name')
            artist = request.form.get('artist')

            print("!!!")
            print(name)
            print(artist)
            print("!!!")

            # posting song to db
            resp = client.update_item(
                TableName=USERS_TABLE,
                Key = {
                    'songId': {'S': song_id},
                    'name': {'S': name},
                    'artist': {'S': artist}
                }
            )


        response_object['message'] = 'Song updated!'

    if request.method == 'DELETE':

        resp = client.get_item(
            TableName = USERS_TABLE,
            Key = {
                'songId': {'S': song_id }
            }
        )
        item = resp.get('Item')

        if not item:
            return jsonify({'error': 'Song does not exist'}), 404

        file_name = item.get('fileName').get('S')

        resp = client.delete_item(
            TableName=USERS_TABLE,
            Key = {
                'songId': {'S': song_id}
            }
        )

        # if not song:
        #     return jsonify({'error': 'Unable to delete song file as it was not found'}), 404

        file_path = os.path.join(BASEDIR, app.config['UPLOAD_FOLDER'], file_name)

        try:
            os.remove(file_path)
        except Exception as e:
            print(e.with_traceback)
            return jsonify({'error': 'Unable to delete song file, please try again'}), 400

        response_object['message'] = 'Song removed!'

    return jsonify(response_object)


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
