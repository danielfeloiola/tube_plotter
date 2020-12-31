from flask import Flask, jsonify, redirect, render_template, request, session
import os, random, string


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Set max file size to 16mb
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Accept gexf files only
app.config['UPLOAD_EXTENSIONS'] = '.gexf'

# folder for uploaded files
app.config['UPLOAD_PATH'] = 'static/uploads'

# set secret key
app.config["SECRET_KEY"] = os.getenv("KEY")

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

        # render the home page
        return render_template("index.html")

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

    # import the plotter to acess the variables
    import plotter

    # if the first image is still being processed
    if plotter.curimg == 1 and plotter.numimages == 0:
        return jsonify("Starting")

    # Get the number of images already processed
    else:

        # format the string for the frontend
        return_str = str(plotter.curimg - 1) + ' of ' + str(plotter.numimages)

        # send away
        return jsonify(return_str)


@app.route("/demo", methods=["GET"])
def demo():
    '''Render a page with the SVG file'''

    return render_template("result.html")


def get_random_string(length):
    '''Makes a random string for the filename'''

    letters = string.ascii_letters
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str
