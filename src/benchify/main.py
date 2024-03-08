import requests
import sys
import time
import jwt
import typer
import webbrowser
import os
import sys

from auth0.authentication.token_verifier \
    import TokenVerifier, AsymmetricSignatureVerifier

from rich import print
from rich.console import Console
from rich.markdown import Markdown

app = typer.Typer()

AUTH0_DOMAIN = 'dev-ig102iz7wc8zzdws.us.auth0.com'
AUTH0_CLIENT_ID = 'ey2Wan6KRIpskOm040sqIVWEIPdKtDVl'
ALGORITHMS = ['RS256']

id_token = None

current_user = None

def validate_token(id_token):
    """
    Verify the token and its precedence
    """
    jwks_url = 'https://{}/.well-known/jwks.json'.format(AUTH0_DOMAIN)
    issuer = 'https://{}/'.format(AUTH0_DOMAIN)
    sv = AsymmetricSignatureVerifier(jwks_url)
    tv = TokenVerifier(
        signature_verifier=sv, 
        issuer=issuer, 
        audience=AUTH0_CLIENT_ID)
    tv.verify(id_token)

def login():
    """
    Runs the device authorization flow and stores the user object in memory
    """
    device_code_payload = {
        'client_id': AUTH0_CLIENT_ID,
        'scope': 'openid profile'
    }
    device_code_response = requests.post(
        'https://{}/oauth/device/code'.format(AUTH0_DOMAIN), 
        data=device_code_payload)

    if device_code_response.status_code != 200:
        print('Error generating the device code')
        raise typer.Exit(code=1)

    print('Device code successful')
    device_code_data = device_code_response.json()

    print(
        '1. On your computer or mobile device navigate to: ', 
        device_code_data['verification_uri_complete'])
    print('2. Enter the following code: ', device_code_data['user_code'])

    try:
        webbrowser.open(device_code_data['verification_uri_complete'])
    except Exception as e:
        pass

    token_payload = {
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
        'device_code': device_code_data['device_code'],
        'client_id': AUTH0_CLIENT_ID
    }

    authenticated = False
    while not authenticated:
        print('Checking if the user completed the flow...')
        token_response = requests.post(
            'https://{}/oauth/token'.format(AUTH0_DOMAIN), data=token_payload)

        token_data = token_response.json()
        if token_response.status_code == 200:
            print('Authenticated!')
            print('- Id Token: {}...'.format(token_data['id_token'][:10]))

            validate_token(token_data['id_token'])
            global current_user
            current_user = jwt.decode(
                token_data['id_token'], 
                algorithms=ALGORITHMS, 
                options={"verify_signature": False})

            authenticated = True
            # Save the current_user.

        elif token_data['error'] not in ('authorization_pending', 'slow_down'):
            print(token_data['error_description'])
            raise typer.Exit(code=1)
        else:
            time.sleep(device_code_data['interval'])

@app.command()
def authenticate():
    if current_user is None:
        login()
    print("<<< SUCCESS : " + str(current_user) + " >>>>")


@app.command()
def analyze():
    file = sys.argv[1]
    
    if current_user is None:
        login()
        print(f"Welcome {current_user['name']}!")
    function_str = None
    
    try:
        with open(file, "r") as fr:
            function_str = fr.read()
    except Exception as e:
        print(f"Encountered exception trying to read {file}: {e}.")
        print("Cannot continue 😢.")
        return
    if function_str == None:
        print(f"Error attempting to read {file}.  Cannot continue 😢.")
        return
    
    console = Console()
    url = "https://benchify.fly.dev/analyze"
    params = {'test_func': function_str, 'current_user': current_user}
    response = requests.get(url, params=params)
    console.print(response.text)

if __name__ == "__main__":
    app()