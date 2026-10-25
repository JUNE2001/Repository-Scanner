import os

import requests
from flask import Flask, redirect, render_template, request, url_for
from flask_cors import CORS

from repository_scanner import code_parser, code_regex, git_parser, parse_repository_url, repository_info

app = Flask(__name__)
CORS(app)


def empty_result(error=None):
    return render_template('index.html',
        Detect_data={'reg': [], 'call': [], 'ip': [], 'ssh_private_key': [], 'openai_api_key': []},
        repo=['', '', ''], Detect_count=0, All_count=0, User_url='', error=error)


@app.route('/')
def main():
    return empty_result()


@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'GET':
        return redirect(url_for('main'))

    user_url = request.form.get('userURL', '').strip()
    try:
        owner, repo_name = parse_repository_url(user_url)
        _, _, branch = repository_info(user_url)
        code_url = git_parser(user_url)
        code_data = code_parser(user_url, code_url)
        data, detect_count, count = code_regex(code_data, code_url)
    except (ValueError, requests.RequestException, KeyError) as exc:
        return empty_result(str(exc)), 400
    return render_template('index.html', Detect_data=data, repo=[owner, repo_name, branch],
        Detect_count=detect_count, All_count=count, User_url=user_url, error=None)


if __name__ == '__main__':
    app.run(host=os.environ.get('HUB_HOST', '127.0.0.1'),
            port=int(os.environ.get('HUB_PORT', '5000')),
            debug=os.environ.get('HUB_DEBUG') == '1')
