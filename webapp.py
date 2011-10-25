import urlparse
import urllib

import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.notestore.NoteStore as NoteStore

import oauth2 as oauth
from flask import Flask, session, redirect, url_for, request


app = Flask(__name__)

APP_SECRET_KEY = \
    'YOUR KEY HERE'

EN_CONSUMER_KEY = 'YOUR KEY HERE'
EN_CONSUMER_SECRET = 'YOUR KEY HERE'

EN_REQUEST_TOKEN_URL = 'https://sandbox.evernote.com/oauth'
EN_ACCESS_TOKEN_URL = 'https://sandbox.evernote.com/oauth'
EN_AUTHORIZE_URL = 'https://sandbox.evernote.com/OAuth.action'

EN_HOST = "sandbox.evernote.com"
EN_USERSTORE_URIBASE = "https://" + EN_HOST + "/edam/user"
EN_NOTESTORE_URIBASE = "https://" + EN_HOST + "/edam/note/"


def get_oauth_client(token=None):
    """Return an instance of the OAuth client."""
    consumer = oauth.Consumer(EN_CONSUMER_KEY, EN_CONSUMER_SECRET)
    if token:
        client = oauth.Client(consumer, token)
    else:
        client = oauth.Client(consumer)
    return client


def get_notestore():
    """Return an instance of the Evernote NoteStore. Assumes that 'shardId' is
    stored in the current session."""
    shardId = session['shardId']
    noteStoreUri = EN_NOTESTORE_URIBASE + shardId
    noteStoreHttpClient = THttpClient.THttpClient(noteStoreUri)
    noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
    noteStore = NoteStore.Client(noteStoreProtocol)
    return noteStore


def get_userstore():
    """Return an instance of the Evernote UserStore."""
    userStoreHttpClient = THttpClient.THttpClient(EN_USERSTORE_URIBASE)
    userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
    userStore = UserStore.Client(userStoreProtocol)
    return userStore


@app.route('/')
def index():
    index_str = '<p><a href="/auth">Authorize this application</a></p>'
    index_str += '<p><a href="/notebook">View a notebook name</a></p>'
    return index_str


@app.route('/auth')
def auth_start():
    """Makes a request to Evernote for the request token then redirects the
    user to Evernote to authorize the application using the request token.

    After authorizing, the user will be redirected back to auth_finish()."""

    client = get_oauth_client()

    # Make the request for the temporary credentials (Request Token)
    callback_url = 'http://%s%s' % ('127.0.0.1:5000', url_for('auth_finish'))
    request_url = '%s?oauth_callback=%s' % (EN_REQUEST_TOKEN_URL,
        urllib.quote(callback_url))

    resp, content = client.request(request_url, 'GET')

    if resp['status'] != '200':
        raise Exception('Invalid response %s.' % resp['status'])

    request_token = dict(urlparse.parse_qsl(content))

    # Save the request token information for later
    session['oauth_token'] = request_token['oauth_token']
    session['oauth_token_secret'] = request_token['oauth_token_secret']

    # Redirect the user to the Evernote authorization URL
    return redirect('%s?oauth_token=%s' % (EN_AUTHORIZE_URL,
        urllib.quote(session['oauth_token'])))


@app.route('/authComplete')
def auth_finish():
    """After the user has authorized this application on Evernote's website,
    they will be redirected back to this URL to finish the process."""

    oauth_verifier = request.args.get('oauth_verifier', '')

    token = oauth.Token(session['oauth_token'], session['oauth_token_secret'])
    token.set_verifier(oauth_verifier)

    client = get_oauth_client()
    client = get_oauth_client(token)

    # Retrieve the token credentials (Access Token) from Evernote
    resp, content = client.request(EN_ACCESS_TOKEN_URL, 'POST')

    if resp['status'] != '200':
        raise Exception('Invalid response %s.' % resp['status'])

    access_token = dict(urlparse.parse_qsl(content))
    authToken = access_token['oauth_token']

    userStore = get_userstore()
    user = userStore.getUser(authToken)

    # Save the users information to so we can make requests later
    session['shardId'] = user.shardId
    session['identifier'] = authToken

    return "<ul><li>oauth_token = %s</li><li>shardId = %s</li></ul>" % (
        authToken, user.shardId)


@app.route('/notebook')
def default_notbook():
    authToken = session['identifier']
    noteStore = get_notestore()
    notebooks = noteStore.listNotebooks(authToken)
    for notebook in notebooks:
            defaultNotebook = notebook
            break

    return defaultNotebook.name


if __name__ == '__main__':
    app.secret_key = APP_SECRET_KEY
    app.run(debug=True)
