from flask import Flask, jsonify, redirect, render_template, request, session
from werkzeug.utils import secure_filename
from flask_session import Session
from datetime import timedelta, datetime
import os, random, string
from tempfile import mkdtemp


# dict to count images
images_counter = dict()


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Set max file size to 16mb
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Accept gexf files only
app.config['UPLOAD_EXTENSIONS'] = '.gexf'

# folder for uploaded files
app.config['UPLOAD_PATH'] = 'static/uploads'

# FIX THIS !!!!!!!!!!
app.config['SECRET_KEY'] = os.getenv("KEY")

# Configure session to use filesystem (instead of signed cookies)
#app.config['SESSION_FILE_DIR'] = mkdtemp()
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SECURE'] = True

Session(app)


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Expires'] = 0
    response.headers['Pragma'] = 'no-cache'
    return response


@app.route('/', methods=['GET', 'POST'])
def index():
    '''Show the main page with instructions'''

    if request.method == 'GET':

        # if there is no session, make one
        if session.get('id') is None:
            id = get_random_string(12)
            session['id'] = id

        # render the home page
        return render_template('index.html')


    elif request.method == 'POST':

        # get file
        f = request.files['file']

        # Handles files from different users > NEEDS FIXING!!!
        file_url = 'static/uploads/visual_export.svg'
        session["file_url"] = file_url

        # check filename and extension
        filename = f.filename
        if filename != '':
            file_ext = os.path.splitext(filename)[1]

            # if the file is not a gexf file show an error message
            if file_ext != app.config['UPLOAD_EXTENSIONS']:
                return jsonify('Please upload a GEFX file')

            # save the file
            f.save(os.path.join(app.config['UPLOAD_PATH'], filename))

        # if the file has no name, return a warning
        else:
            return jsonify('Check filename')

        # set the counter to indicate the analysis started
        images_counter[session.get('id')] = 'Analyzing file'
        print(images_counter[session.get('id')])

        # run plotter
        from plotter import img_plotter
        img_plotter('export', filename)

        # this is not really needed anyway...
        return jsonify('Finished')


@app.route('/results', methods=['GET'])
def results():
    '''Render a page with the SVG file'''

    return render_template('result.html')


@app.route('/counter', methods=['POST'])
def counter():
    '''Make a counter so the progress is displayed on the screen'''

    # get the global dict counter
    global images_counter
    images_processed = images_counter[session.get('id')]

    # if the gefx file is still being processed
    if images_counter[session.get('id')] == 'Analyzing file':
        return jsonify('Analyzing file')

    # if the plotter is already running
    else:
        return jsonify(images_processed)


def get_random_string(length):
    '''Makes a random string for the user id'''

    letters = string.ascii_letters
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str
