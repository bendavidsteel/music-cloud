import uuid
import os
import boto3
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
TRACK_TABLE = os.environ['TRACK_TABLE']
BUCKET = "music-cloud-dev-s3tracks-mdm9dny0wg6g"
IS_OFFLINE = os.environ.get('IS_OFFLINE')
SPOTIFY_CLIENT_ID = "3e0d9d7298e44ab5994a9595100aff22"
SPOTIFY_CLIENT_SECRET = "00bb019487644908b9202a88945259ff"

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CORS_HEADERS'] = 'Content-Type'

# enable CORS
CORS(app)#resources={r"/*": {"origins": "*"}}, send_wildcard=True)


# setting up server for online or offline
# if IS_OFFLINE:
#     db = boto3.client(
#         'dynamodb',
#         region_name='localhost',
#         endpoint_url='http://localhost:8000'
#     )

#     s3 = boto3.client(
#         's3',
#         region_name='localhost',
#         endpoint_url='http://localhost:8001'
#     )
# else:
db = boto3.client('dynamodb',
                  region_name='us-east-1')
s3 = boto3.client('s3',
                  region_name='us-east-1')

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

        #try:
        song_url = "unavailable"

        song_id = uuid.uuid4().hex

        name = request.form.get('name')
        artist = request.form.get('artist')

        fileP = request.form.get('file')

        if fileP == "True":
            file_provided = True

            file_name = name + '--' + artist + '--' + song_id + '.mp3'

            presigned = upload_file_to_s3(file_name, BUCKET)

            response_object['presigned'] = presigned

            song_url = file_name
            playback = True

        else:
            file_provided = False
            playback = False

        # saving song file
        # submitted_file = request.files.get('file')
        # if submitted_file and allowed_filename(submitted_file.filename):

        #     # name_artist = request.form.get('name') + '_' + request.form.get('artist') + '.mp3'

        #     # file_name = secure_filename(name_artist)
        #     file_name = name + '--' + artist + '--' + song_id + '.mp3'

        #     output = upload_file_to_s3(submitted_file, file_name, BUCKET)
        
        #     song_url = file_name

        #     file_provided = True
        #     playback = True
        # else:
        #     file_provided = False
        #     playback = False

        image_url, preview_url, track_id, artist_id, spotify, playback = identify_song(name, artist, file_provided)

        if not file_provided:
            song_url = preview_url

        # posting song to db
        resp = db.put_item(
            TableName=TRACK_TABLE,
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
        

        # except Exception as e:
        #     response_object['error'] = e
        #     response_object['with_traceback'] = e.with_traceback
    
    if request.method == 'GET':
        # fetching songs from db
        resp = db.scan(
            TableName = TRACK_TABLE
        )

        items = resp.get('Items')

        SONGS = []

        for item in items:

            file_provided = item.get('fileProvided').get('BOOL')

            file_name = item.get('songUrl').get('S')

            if file_provided:
                song_url = '%s/%s/%s' % (s3.meta.endpoint_url, BUCKET, file_name)
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

    # allowing cross origin requests
    response = jsonify(response_object)
    # response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/songs/<song_id>', methods=['GET', 'PUT', 'DELETE'])
def single_song(song_id):
    response_object = {'status': 'success'}
    if request.method == "GET":

        resp = db.get_item(
            TableName = TRACK_TABLE,
            Key = {
                'songId': {'S':song_id }
            }
        )
        item = resp.get('Item')

        if not item:
            return jsonify({'error': 'Song does not exist'}), 404

        # delivering file url in s3 bucket
        file_name = item.get('songUrl').get('S')
        
        file_url = '%s/%s/%s' % (s3.meta.endpoint_url, BUCKET, file_name)

        response_object['file_url'] = file_url

        # getting song name
        name = item.get('name').get('S')
        artist = item.get('artist').get('S')

        track_name = name + "--" + artist + '.mp3'

        response_object['file_name'] = track_name

        return jsonify(response_object)
        

    if request.method == 'PUT':

        resp = db.get_item(
            TableName = TRACK_TABLE,
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
        file_provided = item.get('fileProvided').get('BOOL')

        name = request.form.get('name')
        artist = request.form.get('artist')

        # saving song file
        fileP = request.form.get('file')

        print(fileP)

        if fileP == "True":

            print("new file!")

            if not delete_file(file_provided, file_name):
                print("Unable to delete old file")

            file_provided = True

            file_name = name + '--' + artist + '--' + song_id + '.mp3'

            presigned = upload_file_to_s3(file_name, BUCKET)

            response_object['presigned'] = presigned

        image_url, preview_url, track_id, artist_id, spotify, playback = identify_song(name, artist, file_provided)

        if not file_provided:
            file_name = preview_url

        # posting song to db
        resp = db.update_item(
            TableName=TRACK_TABLE,
            Key = {
                'songId': {'S': song_id}
            },
            UpdateExpression="set #n = :n, artist = :a, songUrl = :sU, fileProvided = :fP, imageUrl = :iU, spotifyTrackId = :tI, spotifyArtistId = :aI, spotifyFound = :sF, playback = :p",
            ExpressionAttributeValues={
                ':n': {'S': name},
                ':a': {'S': artist},
                ':sU': {'S': file_name},
                ':fP': {'BOOL': file_provided},
                ':iU': {'S': image_url},
                ':tI': {'S': track_id},
                ':aI': {'S': artist_id},
                ':sF': {'BOOL': spotify},
                ':p': {'BOOL': playback}
            },
            ExpressionAttributeNames={
                '#n': 'name'
            }
        )

        response_object['message'] = 'Song updated!'

    if request.method == 'DELETE':

        try:
            resp = db.get_item(
                TableName = TRACK_TABLE,
                Key = {
                    'songId': {'S': song_id }
                }
            )
            item = resp.get('Item')

            if not item:
                return jsonify({'error': 'Song does not exist'}), 404

            resp = db.delete_item(
                TableName=TRACK_TABLE,
                Key = {
                    'songId': {'S': song_id}
                }
            )

            # if not song:
            #     return jsonify({'error': 'Unable to delete song file as it was not found'}), 404

            file_provided = item.get("fileProvided").get('BOOL')

            file_name = item.get("songUrl").get('S')

            if not delete_file(file_provided, file_name):
                return jsonify({'error': 'Unable to delete song file, please try again'}), 400

            response_object['message'] = 'Song removed!'

        except Exception as e:
            response_object['error'] = e
            response_object['with_traceback'] = e.with_traceback

    # allowing cross origin requests
    response = jsonify(response_object)
    # response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/recommend/<song_id>', methods=['GET'])
def recommend_songs(song_id):

    response_object = {}
    # recommend songs using spotify api

    # get spotify song id from database
    resp = db.get_item(
            TableName = TRACK_TABLE,
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
        response_object['error'] = e

    # allowing cross origin requests
    response = jsonify(response_object)
    # response.headers['Access-Control-Allow-Origin'] = '*'
    return response
    

# upload file to s3 bucket
def upload_file_to_s3(file_name, bucket_name, acl="public-read"):

    try:

        # s3.upload_fileobj(
        #     file,
        #     bucket_name,
        #     file_name,
        #     ExtraArgs={
        #         "ACL": acl,
        #         "ContentType": file.content_type
        #     }
        # )

        presigned = s3.generate_presigned_post(
            bucket_name,
            file_name,
            Fields = {
                "ACL": acl,
                "Content-Type": "audio/mpeg"
            },
            Conditions = [
                ["starts-with", "$Content-Type", ""],
                ["starts-with", "$ACL", ""],
            ],
        )

    except Exception as e:
        print("Something Happened: ", e)
        return e

    # return "{}/{}/{}".format(s3.meta.endpoint_url, BUCKET, file_name)
    return presigned

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

def identify_song(name, artist, file_provided):
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
    preview_url = "none found"
    spotify = False
    playback = False

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
                preview_url = item.get("preview_url")
                playback = True
            else:
                playback = False
        else:
            playback = True

        spotify = True
    except Exception as e:
        print(e)

    return image_url, preview_url, track_id, artist_id, spotify, playback

def delete_file(file_provided, file_name):
    if file_provided:
        try:
            s3.delete_object(
                Bucket = BUCKET,
                Key = file_name
            )
        except Exception as e:
            print(e.with_traceback)
            return False
        finally:
            return True
    else:
        return True

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
