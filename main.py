from flask_restful import Api, Resource, reqparse

from email import header
from operator import methodcaller
import flask
import requests
import base64
from flask import Flask, request
from urllib.parse import urlencode

app = Flask(__name__)
api = Api(app)

client_id = "fc32c15ba50348dcb2eb5a952810b762"
client_secret = "335e44d7968c4cdb8cd980ed04880a70"
base_url = "https://api.spotify.com/v1/"
base_url_accounts = "https://accounts.spotify.com/"
redirect_uri = "http://127.0.0.1:5000/callback"
auth_url = "https://accounts.spotify.com/api/token"
BASEtemp_url = "http://127.0.0.1:5000"

currentAccessToken = ""
userID = ""
selectedPlaylistID = ""

class LoginResource(Resource):
    def get(self):
        return {"data": BASEtemp_url + "/login"}

api.add_resource(LoginResource, "/loginspotify")

def refreshAccess(refresh_token):
    data = {
        "grant_type": "refresh_token",
        'client_id': client_id,
        'client_secret': client_secret,
        "refresh_token": refresh_token,
    }
    response = requests.post(auth_url, data=data)
    #print(response.json())

    return response.json().get("access_token")


@app.route("/login", methods=["GET"])
def login():
    url = base_url_accounts + "authorize?"
    url += urlencode(
                {
               "response_type": 'code',
               "client_id": client_id,
               "scope": "playlist-read-private user-library-read user-read-private user-read-email",
               "redirect_uri": redirect_uri
               })
    return f'<a href="{url}">Login to spotify</a>'


@app.route("/callback", methods=["GET"])
def callback():
    code = request.args.get("code")
    if (not code):
        return "Error"

    data = {
        'grant_type': "authorization_code",
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
    }

    auth_response = requests.post(auth_url, data=data)

    refresh_token = auth_response.json().get('refresh_token')
    #print(auth_response.json())

    global currentAccessToken
    currentAccessToken = refreshAccess(refresh_token)

    return f'<a href="{"http://127.0.0.1:5000/get_playlists"}">playlists</a>'


@app.route("/get_playlists", methods=["GET"])
def get_playlists():
    url = base_url + "me"
    print("This is access token: " + currentAccessToken)
    response = requests.get(url, headers={"Authorization": f"Bearer {currentAccessToken}"})

    global userID
    userID = response.json().get('id')

    url = base_url + "users/" + userID + "/playlists"
    response = requests.get(url, headers={"Authorization": f"Bearer {currentAccessToken}"})

    global selectedPlaylistID
    selectedPlaylistID = response.json().get('items')[0].get('id')

    playlistImageURL = [""]
    #for i in range(0, len(response.json().get('items'))):
        #playlistImageURL[i].append(response.json().get('items')[i].get('images')[0].get('url'))
        #print(playlistImageURL[i])

    #return response.json()
    return f'<a href="{"http://127.0.0.1:5000/analyze"}">Playlist #1 analyze</a>'


@app.route("/analyze", methods=["GET"])
def analyze():
    url = base_url + "playlists/" + selectedPlaylistID
    response = requests.get(url, headers={"Authorization": f"Bearer {currentAccessToken}"})

    trackIDs = []
    for i in range(0, len(response.json().get('tracks').get('items'))):
        trackIDs.append(response.json().get('tracks').get('items')[i].get('track').get('id'))

    for i in range(0, len(trackIDs)):
        print(trackIDs[i])

    ids = ""

    for i in range(0, len(trackIDs)):
        if(i == len(trackIDs) - 1):
            ids = ids + trackIDs[i]
            break
        ids = ids + trackIDs[i] + ","
        
    print(ids)

    #https://www.theinformationlab.co.uk/2019/08/08/getting-audio-features-from-the-spotify-api/
    url = base_url + "audio-features?ids=" + ids

    response = requests.get(url, headers={"Authorization": f"Bearer {currentAccessToken}"})

    # A confidence measure from 0.0 to 1.0 of whether the track is acoustic. 1.0 represents high confidence the track is acoustic.
    avgAcousticness = 0.0

    # Danceability describes how suitable a track is for dancing based on a combination of musical elements including tempo, rhythm stability, beat strength, and overall regularity. A value of 0.0 is least danceable and 1.0 is most danceable.
    avgDanceability = 0.0

    # Energy is a measure from 0.0 to 1.0 and represents a perceptual measure of intensity and activity. Typically, energetic tracks feel fast, loud, and noisy. For example, death metal has high energy, while a Bach prelude scores low on the scale. Perceptual features contributing to this attribute include dynamic range, perceived loudness, timbre, onset rate, and general entropy.
    avgEnergy = 0.0

    # Predicts whether a track contains no vocals. "Ooh" and "aah" sounds are treated as instrumental in this context. Rap or spoken word tracks are clearly "vocal". The closer the instrumentalness value is to 1.0, the greater likelihood the track contains no vocal content. Values above 0.5 are intended to represent instrumental tracks, but confidence is higher as the value approaches 1.0.
    avgInstrumentalness = 0.0

    # Predicts whether a track contains no vocals. "Ooh" and "aah" sounds are treated as instrumental in this context. Rap or spoken word tracks are clearly "vocal". The closer the instrumentalness value is to 1.0, the greater likelihood the track contains no vocal content. Values above 0.5 are intended to represent instrumental tracks, but confidence is higher as the value approaches 1.0.
    avgLiveness = 0.0

    # The overall loudness of a track in decibels (dB). Loudness values are averaged across the entire track and are useful for comparing relative loudness of tracks. Loudness is the quality of a sound that is the primary psychological correlate of physical strength (amplitude). Values typically range between -60 and 0 db.
    avgLoudness = 0.0

    # Speechiness detects the presence of spoken words in a track. The more exclusively speech-like the recording (e.g. talk show, audio book, poetry), the closer to 1.0 the attribute value. Values above 0.66 describe tracks that are probably made entirely of spoken words. Values between 0.33 and 0.66 describe tracks that may contain both music and speech, either in sections or layered, including such cases as rap music. Values below 0.33 most likely represent music and other non-speech-like tracks.
    avgSpeechiness = 0.0

    # A measure from 0.0 to 1.0 describing the musical positiveness conveyed by a track. Tracks with high valence sound more positive (e.g. happy, cheerful, euphoric), while tracks with low valence sound more negative (e.g. sad, depressed, angry).
    avgValence = 0.0

    for i in range(0, len(response.json().get('audio_features'))):
        avgAcousticness += (response.json().get('audio_features')[i].get('acousticness'))
        avgDanceability += (response.json().get('audio_features')[i].get('danceability'))
        avgEnergy += (response.json().get('audio_features')[i].get('energy'))
        avgInstrumentalness += (response.json().get('audio_features')[i].get('instrumentalness'))
        avgLiveness += (response.json().get('audio_features')[i].get('liveness'))
        avgLoudness += (response.json().get('audio_features')[i].get('loudness'))
        avgSpeechiness += (response.json().get('audio_features')[i].get('speechiness'))
        avgValence += (response.json().get('audio_features')[i].get('valence'))

    avgAcousticness = avgAcousticness / len(response.json().get('audio_features'))
    avgDanceability = avgDanceability / len(response.json().get('audio_features'))
    avgEnergy = avgEnergy / len(response.json().get('audio_features'))
    avgInstrumentalness = avgInstrumentalness / len(response.json().get('audio_features'))
    avgLiveness = avgLiveness / len(response.json().get('audio_features'))
    avgLoudness = avgLoudness / len(response.json().get('audio_features'))
    avgSpeechiness = avgSpeechiness / len(response.json().get('audio_features'))
    avgValence = avgValence / len(response.json().get('audio_features'))

    print(avgAcousticness, " | ", avgDanceability, " | ", avgEnergy, " | ", avgInstrumentalness, " | ", avgLiveness, " | ", avgLoudness, " | ", avgSpeechiness, " | ", avgValence)

    return response.json()


if __name__ == "__main__":
    app.run(debug=True)