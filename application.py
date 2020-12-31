from flask import Flask, jsonify, redirect, render_template, request, session
import os, random, string


# dict to count images
images_counter = dict()


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Uploads settings
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = '.gexf'
app.config['UPLOAD_PATH'] = 'static/uploads'

# Setting the secret key
app.config['SECRET_KEY'] = os.getenv("KEY")

# Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_FILE_DIR'] = mkdtemp()
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SECURE'] = True
Session(app)


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    """Show the main page with instructions"""

    if request.method == "GET":

        # if there is no session, make one
        if session.get('id') is None:
            id = get_random_string(12)
            session['id'] = id
            print(session['id'])

        # render the home page
        return render_template('index.html')

    elif request.method == "POST":

        # TODO: settings menu

        # get file
        f = request.files['file']

        # check filename and extension
        filename = f.filename
        if filename != '':
            file_ext = os.path.splitext(filename)[1]

            # if the format is not a gexf file
            if file_ext != app.config['UPLOAD_EXTENSIONS']:

                # show error mesage
                return jsonify("Please upload a GEFX file")


            # save the file
            f.save(os.path.join(app.config['UPLOAD_PATH'], filename))

        # if the file has no name
        else:
            # warning: file must have a name
            return jsonify("Check filename")


        # making a random id/filename
        id = get_random_string(12)
        file_url = 'static/uploads/visual_export.svg'

        # add the id to the session
        session["id"] = id
        session["file_url"] = file_url

        # get the plotter ready
        import plotter

        # reset variables for every file submitted
        plotter.curimg = 1
        plotter.numimages = 0

        # and run
        plotter.img_plotter("export", filename)

        # json to display the results page
        return jsonify("Finished")


@app.route("/results", methods=["GET"])
def results():
    '''Render a page with the SVG file'''

    return render_template("result.html")

@app.route("/counter", methods=["POST"])
def counter():
    '''Make a counter so the progress is displayed on the screen'''

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


    else:
        return jsonify(images_processed)



@app.route("/demo", methods=["GET"])
def demo():
    '''Render a page with the SVG file'''

    return render_template("demo.html")


def get_random_string(length):
    '''Makes a random string for the filename'''

    letters = string.ascii_letters
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str
