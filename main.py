from configparser import ConfigParser
import base64
import string
import  random
import hashlib
import requests
from flask import Flask, request, redirect, session,jsonify
import urllib



# Import to pull values from config file
config = ConfigParser()
keys = ConfigParser()
config.read_file(open("config.txt"))
keys.read_file(open('secrets.txt'))

# Define some key values into variables
base_account_url = config.get("STATIC",'base_account_url');
base_api_url = config.get("STATIC","base_api_url");
client_id = keys.get('KEYS','client_id');
client_secret = keys.get('KEYS','client_secret');
secret_key = keys.get('KEYS','secret_key');
redirect_uri = config.get('STATIC','redirect_uri');

################################################
# Create Flask server for URI and redirect

## Create a class to manage verifier/challenge generation
class OAuth_String():
    def __init__(self):
        self.code_verifier = self.code_verifier()
        self.code_challenge = self.code_challenge(self.code_verifier)
    def code_verifier(self, length=128):
        possible_characters = string.ascii_letters + string.digits + "-._~";
        return ''.join(random.choice(possible_characters) for _ in range(length))

    def code_challenge(self,code_verifier):
        sha256_hash = hashlib.sha256(code_verifier.encode()).digest()
        return base64.urlsafe_b64encode(sha256_hash).decode().rstrip('=')

#Create an instance
oauth_string = OAuth_String()

app = Flask(__name__);

app.secret_key = f'{secret_key}'

## Route to trigger sign in flow to get token
@app.route('/login')
def login():
    url =  base_account_url + "authorize" 
    
    session['code_verifier'] = oauth_string.code_verifier
    session['code_challenge'] = oauth_string.code_challenge
    
    #print (session['code_verifier'])
    
    body = {
        "client_id": client_id,
        "response_type": 'code',
        "redirect_uri": redirect_uri,
        "code_challenge_method": 'S256',
        "code_challenge": session['code_challenge']
        
    }
    
    authorizationUrl = f"{url}?{urllib.parse.urlencode(body)}"
    return redirect(authorizationUrl)
    
@app.route('/callback')
def callback():
    code = request.args.get('code')
    code_verifier = session.get('code_verifier')
    
    
    if not code or not code_verifier:
        return jsonify({"error": "Missing code or code verifier"}), 400
    
    try:
        access = exchange_code_for_token(code, code_verifier);
        access_token = access['access_token']
        refresh_token = access['refresh_token']
        
        db_server_url = 'http://127.0.0.1:5000/store'
        response = requests.post(db_server_url, json={"access_token": access_token, "refresh_token":refresh_token})
        print(response)
        print('Above is respone')
        #if response.status_code == 200:
         #   return jsonify({"message": "Access token stored."})
        #else:
         #   return jsonify({"error":"Failed to store token"}), 500  
    except Exception as e:
        return jsonify({"error": str(e)}),500
    return access

def exchange_code_for_token(code, code_verifier):
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,  # Replace with your actual redirect URI
        'client_id': client_id,        
        'client_secret': client_secret,  # Replace with your actual client secret
        'code_verifier': code_verifier
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json()  # Contains access token and possibly refresh token


    

## This should be the secure route to retrieve token 
""""
@app.route('/accesstoken')
def accessToken(code):
    url = base_account_url + 'api/token'
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    
    }
    form = {
        "grant_type": 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'code_verifier': oauth_string.base64String
    }
    
    response = requests.post(url, headers=headers, data=form)
    print(response)
    return response
"""
if __name__ =='__main__':
    app.run(port=8080, debug=True)
##############################################
#access_token = getAccessToken(base_account_url, client_id, client_secret)
#print(access_token)
#top_object = getTopItems(base_api_url, access_token, 'artists', 'long_term', 10, 5)



    
