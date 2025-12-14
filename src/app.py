from flask import Flask, redirect, request, session, url_for
import os
import requests

app = Flask(__name__)

# Secret key to secure session data
app.secret_key = os.urandom(24)

# OAuth configuration
CLIENT_ID = os.getenv('ROBUX_OAUTH_CLIENT_ID')
CLIENT_SECRET = os.getenv('ROBUX_OAUTH_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

# Step 1: Redirect to Roblox OAuth
@app.route('/auth/roblox')
def auth_roblox():
    auth_url = f"https://apis.roblox.com/oauth/v1/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identity"
    return redirect(auth_url)

# Step 2: Handle the OAuth callback
@app.route('/auth/roblox/callback')
def auth_roblox_callback():
    code = request.args.get('code')

    if code:
        # Exchange the authorization code for an access token
        token_url = "https://apis.roblox.com/oauth/v1/token"
        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(token_url, data=data)
        response_data = response.json()

        if 'access_token' in response_data:
            session['access_token'] = response_data['access_token']
            return "Successfully authenticated with Roblox!"
        else:
            return "Error authenticating with Roblox.", 400
    return "No code received.", 400

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8000)  # Make sure it's accessible externally
