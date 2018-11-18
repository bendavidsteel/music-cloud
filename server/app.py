import uuid
import os
import boto3
import botocore
import requests
import urllib
import base64
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
SPOTIFY_CLIENT_ID = "3e0d9d7298e44ab5994a9595100aff22"
SPOTIFY_CLIENT_SECRET = "00bb019487644908b9202a88945259ff"

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

        song_url = "unavailable"

        # saving song file
        submitted_file = request.files.get('file')
        if submitted_file and allowed_filename(submitted_file.filename):

            name_artist = request.form.get('name') + '_' + request.form.get('artist') + '.mp3'

            file_name = secure_filename(name_artist)

            output = upload_file_to_s3(submitted_file, file_name, BUCKET_NAME)
        
            song_url = file_name

            file_provided = True
            playback = True
        else:
            file_provided = False
            playback = False



        song_id = uuid.uuid4().hex
        name = request.form.get('name')
        artist = request.form.get('artist')

        token = get_access_token()

        # using spotify api to get album cover
        query = {'q': 'track:' + name + ' ' + 'artist:' + artist, 'type': 'track', 'limit': '1'}
        query = urllib.parse.urlencode(query, quote_via=urllib.parse.quote)

        header = {'Authorization': 'Bearer ' + token}

        spotify_url = "https://api.spotify.com/v1/search"

        response = requests.get(spotify_url, params=query, headers=header)
        
        image_url = "none found"
        track_id = "none found"
        artist_id = "none found"
        spotify = False

        try:
        # parsing response
            data = response.json()
            
            item = data.get("tracks").get("items")[0]

            artist_id = item.get("album").get("artists")[0].get("id")

            track_id = item.get("id")

            covers = item.get("album").get("images")

            image_url = covers[1].get("url")

            if not file_provided:
                if item.get("preview_url") != None:
                    song_url = item.get("preview_url")
                    playback = True
                else:
                    playback = False

            spotify = True
        except Exception as e:
            print(e)

        print(song_url)

        # posting song to db
        resp = db.put_item(
            TableName=USERS_TABLE,
            Item = {
                'songId': {'S': song_id},
                'name': {'S': name},
                'artist': {'S': artist},
                'songUrl': {'S': song_url},
                'fileProvided': {'BOOL': file_provided},
                'playback': {'BOOL': playback},
                'spotifyFound': {'BOOL': spotify},
                'imageUrl': {'S': image_url},
                'spotifyTrackId': {'S': track_id},
                'spotifyArtistId': {'S': artist_id}
            }
        )

        response_object['message'] = 'Song added!'
    
    if request.method == 'GET':
        # fetching songs from db
        resp = db.scan(
            TableName = USERS_TABLE
        )

        items = resp.get('Items')

        SONGS = []

        for item in items:

            file_provided = item.get('fileProvided').get('BOOL')

            file_name = item.get('songUrl').get('S')

            if file_provided:
                song_url = '%s/%s/%s' % (s3.meta.endpoint_url, BUCKET_NAME, file_name)
            else:
                song_url = file_name

            SONGS.append({
                'id': item.get('songId').get('S'),
                'name': item.get('name').get('S'),
                'artist': item.get('artist').get('S'),
                'file': song_url,
                'spotify_found': item.get('spotifyFound').get('BOOL'),
                'file_provided': file_provided,
                'playback': item.get('playback').get('BOOL'),
                'image_url': item.get('imageUrl').get('S')
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

        file_name = item.get('songUrl').get('S')
        
        file_url = '%s/%s/%s' % (s3.meta.endpoint_url, BUCKET_NAME, file_name)

        response_object['file_url'] = file_url

        # # try:
        # obj = s3.get_object(
        #     Bucket = BUCKET_NAME,
        #     Key = file_name
        # )

        # fileobj = obj['Body']

        # response = send_file(fileobj, 
        #                         as_attachment=True,
        #                         attachment_filename=file_name,
        #                         mimetype='audio/mpeg')
        
        # response_object.headers.add('Access-Control-Allow-Origin', '*')

        return jsonify(response_object)
        
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
        file_name = item.get('songUrl').get('S')

        name = request.form.get('name')
        artist = request.form.get('artist')

        # saving song file
        submitted_file = request.files.get('file')
        if submitted_file and allowed_filename(submitted_file.filename):

            name_artist = request.form.get('name') + '_' + request.form.get('artist') + '.mp3'

            file_name = secure_filename(name_artist)

            output = upload_file_to_s3(submitted_file, file_name, BUCKET_NAME)


        # posting song to db
        resp = db.update_item(
            TableName=USERS_TABLE,
            Key = {
                'songId': {'S': song_id}
            },
            UpdateExpression="set #n = :n, artist = :a, songUrl = :f",
            ExpressionAttributeValues={
                ':n': {'S': name},
                ':a': {'S': artist},
                ':f': {'S': file_name}
            },
            ExpressionAttributeNames={
                '#n': 'name'
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

        resp = db.delete_item(
            TableName=USERS_TABLE,
            Key = {
                'songId': {'S': song_id}
            }
        )

        # if not song:
        #     return jsonify({'error': 'Unable to delete song file as it was not found'}), 404

        if item.get("fileProvided"):

            file_name = item.get("song_url")
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

@app.route('/recommend/<song_id>', methods=['GET'])
def recommend_songs(song_id):

    response_object = {}
    # recommend songs using spotify api

    # get spotify song id from database
    resp = db.get_item(
            TableName = USERS_TABLE,
            Key = {
                'songId': {'S':song_id }
            }
        )
    item = resp.get('Item')

    if not item:
        return jsonify({'error': 'Song does not exist'}), 404

    spotify_track_id = item.get('spotifyTrackId').get('S')
    spotify_artist_id = item.get('spotifyArtistId').get('S')

    token = get_access_token()

    # using spotify api to get album cover
    query = {'seed_artists': spotify_artist_id, 'seed_tracks': spotify_track_id, 'limit': '3'}
    query = urllib.parse.urlencode(query, quote_via=urllib.parse.quote)

    header = {'Authorization': 'Bearer ' + token}

    spotify_url = "https://api.spotify.com/v1/recommendations"

    response = requests.get(spotify_url, params=query, headers=header)

    SONGS = []

    try:
        # parsing response
        data = response.json()
        

        # sending songs
        for track in data.get("tracks"):

            name = track.get("name")
            artist = track.get("artists")[0].get("name")
            link = track.get("external_urls").get("spotify")
            image_url = track.get("album").get("images")[1].get("url")
            if track.get("preview_url") != None:
                preview_url = track.get("preview_url")
            else:
                preview_url = "no sample"

            SONGS.append({
                'name': name,
                'artist': artist,
                'image_url': image_url,
                'spotify_url': link,
                'preview_url': preview_url
            })

        response_object['songs'] = SONGS

    except Exception as e:
        print(e)

    return jsonify(response_object)
    

# upload file to s3 bucket
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

# replace spaces with %20 characters
def replace_spaces(string):
    return string.replace(' ', '%20')

# get access token from spotify api
def get_access_token():
    # obtaining spotify authentification
    client_str = SPOTIFY_CLIENT_ID + ":" + SPOTIFY_CLIENT_SECRET
    client64 = base64.b64encode(client_str.encode("utf-8"))

    body = {'grant_type': 'client_credentials'}
    header = {'Authorization': 'Basic ' + client64.decode("utf-8")}

    spotify_token_url = 'https://accounts.spotify.com/api/token'

    response = requests.post(spotify_token_url, data=body, headers=header)

    data = response.json()

    return data.get("access_token")

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
