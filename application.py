from flask import Flask, jsonify, redirect, render_template, request, session
from werkzeug.utils import secure_filename
from flask_session import Session
from datetime import timedelta, datetime
import os, random, string
from tempfile import mkdtemp

# import the svg plotter
from svg_plot import svg_plotter

# dict to count images
images_counter = dict()

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Uploads settings
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.gexf', '.svg']
app.config['UPLOAD_PATH'] = 'static/uploads'
app.config['SESSION_COOKIE_SECURE'] = True

# Setting the secret key
#app.config['SECRET_KEY'] = os.getenv("KEY")
app.secret_key = os.getenv("KEY")


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

        # render the home page
        return render_template('index.html')

    elif request.method == 'POST':


        # if there is no session, make one
        if session.get('id') is None:

            # generate a ramdom string as a session id
            session['id'] = get_random_string(12)
            #session['type'] = 'none yet'


        # get the file uploaded file
        f = request.files['file']

        # sets the output file name and stores in the session
        session["file_url"] = "static/uploads/visual_" + session.get('id') + ".svg"

        # check filename and extension
        filename = f.filename
        if filename != '':
            file_ext = os.path.splitext(filename)[1]

            # if the file type is not supported show an error message
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                return jsonify('Please check file extension')

            # save the file
            f.save(os.path.join(app.config['UPLOAD_PATH'], filename))

        # if the file has no name, return a warning
        else:
            return jsonify('Check filename')


        # if a graph file is uploaded, also sets up the counter
        if file_ext == '.gexf':

            # set the counter to indicate the analysis started
            images_counter[session.get('id')] = 'Analyzing file'
            session['type'] = 'gexf'

            # run plotter
            from plotter import img_plotter
            img_plotter('export', filename)

            # return nothing
            return('', 204)

        # if a svg file is uploaded, just get the name and start
        elif file_ext == '.svg':

            # get the path for the uploaded file
            uploaded_file = 'static/uploads/' + filename

            # adjust session so it won't count images if svg file is uploaded
            session['type'] = 'svg'

            # call plotter function
            svg_plotter(uploaded_file, session["file_url"])

            # return nothing
            return('', 204)


@app.route('/results', methods=['GET'])
def results():
    '''Render a page with the SVG file'''

    return render_template('result.html')


@app.route('/counter', methods=['POST'])
def counter():
    '''Make a counter so the progress is displayed on the screen'''

    # # DEBUG:
    print("DEBUG: >>>>>>>>>>>>>>>" + session.get('type'))

    # skips the count if processing a svg file
    if session.get('type') == 'svg':

        return jsonify('Finished')

    # else: proceed with the counter
    elif session.get('type') == 'gexf':

        # get the global dict counter
        global images_counter
        images_processed = images_counter[session.get('id')]

        # if the process already started
        if images_processed != 'Analyzing file':
            result = images_processed.split(" of ")
            completed = result[0]
            total = result[1]

            # if completed, return finish to display the results on th frontend
            if completed == total:
                return jsonify('Finished')
            else:
                return jsonify(images_processed)

        # returns just so the function wont return a error
        else:
            return jsonify(images_processed)


def get_random_string(length):
    '''Makes a random string for the user id'''

    return ''.join(random.choice(string.ascii_letters) for i in range(length))


@app.route("/demo", methods=["GET"])
def demo():
    '''Render a page with the demo SVG file'''

    return render_template("demo.html")
