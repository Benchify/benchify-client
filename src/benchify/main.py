import requests
import sys

from rich import print
from rich.console import Console
from rich.markdown import Markdown

def send_request(function_str, api_key):
    console = Console()
    url = "https://benchify.fly.dev/analyze"
    params = {'test_func': function_str, 'api_key': api_key}
    response = requests.get(url, params=params)
    md = Markdown(response.text)
    console.print(md)
    return md