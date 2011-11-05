Introduction
============

This is a simple [Flask][1]. web app that demonstrates how to access the
[Evernote API][2] using OAuth.

[1]: http://flask.pocoo.org/
[2]: https://www.evernote.com/about/developer/api/

Setup
=====

    virtualenv --no-site-packages testapp
    cd testapp/
    git clone git://github.com/dasevilla/evernote-oauth-example.git
    cd evernote-oauth-example
    source bin/activate
    pip install -r reqs.txt
