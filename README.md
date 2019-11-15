# MinigameDungeonServer

## Build instructions
Since this is a Python 3.7.3 program, there is no need to build.
However, this program requires, in python3:

```
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
pip install py3-validate-email
pip install flask
pip install requests
```

Then, to run the program, given python points to Python 3.7.3, use:

```
python server.py
```

To run with the gunicorn wsgi gateway, first install gunicorn using:

```
pip install gunicorn
```

Then, run using:

```
gunicorn --bind=0.0.0.0:42069 server:app
```
