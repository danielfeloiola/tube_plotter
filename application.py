from flask import Flask, jsonify, render_template, session, request #redirect.
#from werkzeug.utils import secure_filename
#from flask_session import Session
#from datetime import timedelta, datetime
import os, random, string
#from tempfile import mkdtemp

# dict to count images
images_counter = dict()

# Configure application
app = Flask(__name__)

# Uploads settings
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.gexf', '.svg']
app.config['UPLOAD_PATH'] = 'static/uploads'
app.config['SESSION_COOKIE_SECURE'] = True

# Setting the secret key
app.secret_key = os.getenv("KEY")

print("Debugger test")


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

        # make an id and render the page
        session['id'] = get_random_string(12)
        return render_template('index.html')

    elif request.method == 'POST':

        # get the file uploaded file
        f = request.files['file']

        # make directories and add them to the cookies for later
        images_folder = f"static/images/{session.get('id')}"
        directory = os.mkdir(images_folder)
        session["file_url"] = "static/svg/visual_" + session.get('id') + ".svg"
        session["zip_url"] = "static/images/" + session.get('id') + ".zip"

        # check filename and extension: if the file has a name
        filename = f.filename
        if filename != '':

            # get the file extension and check id its supported, if so then save
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                return jsonify('Please check file extension')
            f.save(os.path.join(app.config['UPLOAD_PATH'], filename))

        # else if the file has no name, return a warning
        else:
            return jsonify('Check filename')


        # if a graph file is uploaded, also sets up the counter
        if file_ext == '.gexf':

            # set the counter to indicate the analysis started
            images_counter[session.get('id')] = 'Analyzing file'

            # run plotter
            from plotter import img_plotter
            img_plotter(filename, images_folder)

            # return nothing
            return('', 204)

        # if a svg file is uploaded, just get the name and start
        elif file_ext == '.svg':

            # get the path for the uploaded file
            uploaded_file = 'static/uploads/' + filename

            # adjust session so it won't count images if svg file is uploaded
            images_counter[session.get('id')] = 'skip'

            # import the svg plotter and run
            from svg_plot import svg_plotter
            svg_plotter(uploaded_file, session["file_url"])

            # return nothing
            return('', 204)


@app.route('/results', methods=['GET'])
def results():
    '''Render a page with the SVG file. Zips the folder for download'''


    import shutil
    # the zip will live inside the images folder too
    name = f"static/images/{session.get('id')}"
    shutil.make_archive(name, 'zip', name)

    return render_template('result.html')


@app.route('/counter', methods=['GET', 'POST'])
def counter():
    '''Make a counter so the progress is displayed on the screen'''

    # get the global dict counter
    global images_counter

    # if uploading a svg file, skip the countig and show the result link
    if images_counter[session.get('id')] == 'skip':
        return jsonify('Finished')

    # if uploading a gexf, do the counting
    else:

        # look into the dict for the id
        images_processed = images_counter[session.get('id')]

        # if the process already started
        if images_processed != 'Analyzing file':
            result = images_processed.split(" of ")
            completed = result[0]
            total = result[1]

            # if completed return finished to display the results
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
