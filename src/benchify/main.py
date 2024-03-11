import requests
import sys
import time
import jwt
import typer
import webbrowser
import os
import sys
import ast
import json

from auth0.authentication.token_verifier \
    import TokenVerifier, AsymmetricSignatureVerifier

from rich import print
from rich.console import Console
from rich.markdown import Markdown

app = typer.Typer()

AUTH0_DOMAIN    = 'benchify.us.auth0.com'
AUTH0_CLIENT_ID = 'VessO49JLtBhlVXvwbCDkeXZX4mHNLFs'
ALGORITHMS      = ['RS256']
id_token        = None
current_user    = None

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
        print('Authenticating ...')
        token_response = requests.post(
            'https://{}/oauth/token'.format(AUTH0_DOMAIN), data=token_payload)

        token_data = token_response.json()
        if token_response.status_code == 200:
            print('✅ Authenticated!')
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
    print("✅ Logged in " + str(current_user))

def get_function_source(ast_tree, function_name, code):
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            start_line = node.lineno
            end_line = node.end_lineno
            function_source = '\n'.join(
                code.splitlines()[start_line - 1:end_line])
            return function_source
    # Return None if the function was not found
    return None

@app.command()
def analyze():
    if len(sys.argv) == 1:
        print("⬇️ Please specify the file to be analyzed.")
        return

    file = sys.argv[1]
    
    if current_user is None:
        login()
        print(f"Welcome {current_user['name']}!")
    function_str = None
    
    try:
        print("Scanning " + file + " ...")
        with open(file, "r") as fr:
            function_str = fr.read()
            # is there more than one function in the file?
            if function_str.count("def ") > 1:
                if len(sys.argv) == 2:
                    print("Since there is more than one function in the " + \
                        "file, please specify which one you want to " + \
                        "analyze, e.g., \n$ benchify sortlib.py isort")
                    return
                else:
                    tree = ast.parse(function_str)
                    function_str = get_function_source(
                        tree, sys.argv[2], function_str)
                    if function_str:
                        pass
                    else:
                        print(f"🔍 Function named {sys.argv[1]} not " + \
                            f"found in {sys.argv[0]}.")
                        return
    except Exception as e:
        print(f"Encountered exception trying to read {file}: {e}." + \
            " Cannot continue 😢.")
        return
    if function_str == None:
        print(f"Error attempting to read {file}." + \
            " Cannot continue 😢.")
        return
    
    console = Console()
    url = "https://benchify.fly.dev/analyze"
    params = {'test_func': function_str, 'current_user': current_user}
    print("Analyzing.  Should take about 1 minute ...")
    response = requests.get(url, params=params)
    console.print(response.text)

if __name__ == "__main__":
    app()