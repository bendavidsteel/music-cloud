import uuid
import os
import boto3
import botocore
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
BUCKET_NAME = 'local-bucket'

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['S3_LOCATION'] = 'http://localhost:8001/'

# setting up server for online or offline
if IS_OFFLINE:
    db = boto3.client(
        'dynamodb',
        region_name='localhost',
        endpoint_url='http://localhost:8000'
    )

    s3 = boto3.client(
        's3',
        region_name='localhost',
        endpoint_url='http://localhost:8001'
    )
else:
    db = boto3.client('dynamodb')
    s3 = boto3.client('s3')

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
            resp = db.put_item(
                TableName=USERS_TABLE,
                Item = {
                    'songId': {'S': song_id},
                    'name': {'S': name},
                    'artist': {'S': artist},
                    'fileName': {'S': file_name}
                }
            )

            output = upload_file_to_s3(submitted_file, file_name, BUCKET_NAME)
            print(output)
        else:
            return jsonify({'error': 'Please provide valid file'}),400

        response_object['message'] = 'Song added!'
    
    if request.method == 'GET':
        # fetching songs from db
        resp = db.scan(
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

        resp = db.get_item(
            TableName = USERS_TABLE,
            Key = {
                'songId': {'S':song_id }
            }
        )
        item = resp.get('Item')

        if not item:
            return jsonify({'error': 'Song does not exist'}), 404

        file_name = item.get('fileName').get('S')
        
        # try:
        obj = s3.get_object(
            Bucket = BUCKET_NAME,
            Key = file_name
        )

        fileobj = obj['Body']

        response = send_file(fileobj, 
                                as_attachment=True,
                                attachment_filename=file_name,
                                mimetype='audio/mpeg')
        
        response.headers.add('Access-Control-Allow-Origin', '*')

        return response
        
        # except Exception as e:
        #     print(e)
        #     return jsonify({'error': 'Unable to deliver song file'}), 400

        


    if request.method == 'PUT':

        resp = db.get_item(
            TableName = USERS_TABLE,
            Key = {
                'songId': {'S':song_id }
            }
        )
        item = resp.get('Item')

        if not item:
            return jsonify({'error': 'Song does not exist'}), 404

        name= item.get('name').get('S')
        artist = item.get('artist').get('S')
        file_name = item.get('fileName').get('S')

        # saving song file
        submitted_file = request.files.get('file')
        if submitted_file and allowed_filename(submitted_file.filename):

            name_artist = request.form.get('name') + '_' + request.form.get('artist') + '.mp3'

            file_name = secure_filename(name_artist)

            name = request.form.get('name')
            artist = request.form.get('artist')

            output = upload_file_to_s3(submitted_file, file_name, BUCKET_NAME)
            print(output)
        else:
            name = request.form.get('name')
            artist = request.form.get('artist')


        # posting song to db
        resp = db.update_item(
            TableName=USERS_TABLE,
            Key = {
                'songId': {'S': song_id},
                'name': {'S': name},
                'artist': {'S': artist},
                'fileName': {'S': file_name}
            }
        )

        response_object['message'] = 'Song updated!'

    if request.method == 'DELETE':

        resp = db.get_item(
            TableName = USERS_TABLE,
            Key = {
                'songId': {'S': song_id }
            }
        )
        item = resp.get('Item')

        if not item:
            return jsonify({'error': 'Song does not exist'}), 404

        file_name = item.get('fileName').get('S')

        resp = db.delete_item(
            TableName=USERS_TABLE,
            Key = {
                'songId': {'S': song_id}
            }
        )

        # if not song:
        #     return jsonify({'error': 'Unable to delete song file as it was not found'}), 404

        try:
            s3.delete_object(
                Bucket = BUCKET_NAME,
                Key = file_name
            )
        except Exception as e:
            print(e.with_traceback)
            return jsonify({'error': 'Unable to delete song file, please try again'}), 400

        response_object['message'] = 'Song removed!'

    return jsonify(response_object)

def upload_file_to_s3(file, file_name, bucket_name, acl="public-read"):

    try:

        s3.upload_fileobj(
            file,
            bucket_name,
            file_name,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )

    except Exception as e:
        print("Something Happened: ", e)
        return e

    return "{}{}/{}".format(app.config["S3_LOCATION"], BUCKET_NAME, file_name)



if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
