from flask import Flask, request, redirect
import requests
import json
import os
import secrets

app = Flask(__name__)

# Configuration
CLIENT_ID = '6734083560814458935'
CLIENT_SECRET = 'RBX-7ZOWmqVYpkCKs7mHDrcBFn7mvK24kF7KYzwrZvToprwX5IPLk3uyTSgZJ7eYQeBq'
REDIRECT_URI = 'https://roblox-oauth-zx1j.onrender.com/auth/roblox/callback'

# Store pending verifications and verified users in memory
pending_verifications = {}
verified_users = {}

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Roblox OAuth Service</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                text-align: center;
            }
            h1 { color: #667eea; }
            .status { color: #4CAF50; font-size: 24px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔗 Roblox OAuth Service</h1>
            <div class="status">✅ Server is running!</div>
            <p>Use the Discord bot to verify your account.</p>
        </div>
    </body>
    </html>
    """

@app.route('/verify')
def start_verification():
    discord_id = request.args.get('discord_id')
    discord_name = request.args.get('discord_name', 'Unknown')
    
    if not discord_id:
        return "Missing discord_id parameter", 400
    
    state = secrets.token_urlsafe(32)
    pending_verifications[state] = {
        'discord_id': discord_id,
        'discord_name': discord_name
    }
    
    oauth_url = (
        f"https://apis.roblox.com/oauth/v1/authorize?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope=openid%20profile&"
        f"response_type=code&"
        f"state={state}"
    )
    
    return redirect(oauth_url)

@app.route('/auth/roblox/callback')
def roblox_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return render_html(f"Authorization failed: {error}", False)
    
    if not code or not state:
        return render_html("Missing required parameters", False)
    
    if state not in pending_verifications:
        return render_html("Invalid or expired verification", False)
    
    try:
        token_response = requests.post(
            'https://apis.roblox.com/oauth/v1/token',
            data={
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'code': code
            },
            timeout=10
        )
        
        if token_response.status_code != 200:
            return render_html(f"Token exchange failed", False)
        
        access_token = token_response.json()['access_token']
        
        user_response = requests.get(
            'https://apis.roblox.com/oauth/v1/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        
        if user_response.status_code != 200:
            return render_html("Failed to get user info", False)
        
        user_info = user_response.json()
        roblox_username = user_info['preferred_username']
        roblox_id = user_info['sub']
        
        pending = pending_verifications[state]
        discord_id = pending['discord_id']
        discord_name = pending['discord_name']
        
        verified_users[str(discord_id)] = {
            'discord_username': discord_name,
            'roblox_username': roblox_username,
            'roblox_id': roblox_id
        }
        
        del pending_verifications[state]
        
        return render_html(f"Your Roblox account <strong>{roblox_username}</strong> has been successfully linked!", True)
        
    except Exception as e:
        return render_html(f"Error: {str(e)}", False)

@app.route('/api/verified/<discord_id>')
def check_verified(discord_id):
    if str(discord_id) in verified_users:
        return verified_users[str(discord_id)]
    return {'error': 'Not verified'}, 404

@app.route('/api/all-verified')
def get_all_verified():
    return verified_users

def render_html(message, success):
    color = "#4CAF50" if success else "#f44336"
    bg_gradient = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)" if success else "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
    icon = "✅" if success else "❌"
    title = "Verification Successful!" if success else "Verification Failed"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: {bg_gradient};
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 500px;
            }}
            h1 {{ color: {color}; margin-bottom: 20px; }}
            p {{ color: #666; font-size: 18px; line-height: 1.6; }}
            .icon {{ font-size: 72px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">{icon}</div>
            <h1>{title}</h1>
            <p>{message}</p>
            <p>You can now close this window and return to Discord.</p>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
