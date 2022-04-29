# important stuff
from flask import Flask, jsonify, render_template, session, request
import os


# dict to count images
images_counter = dict()


# Configure application
app = Flask(__name__)


# settings
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.gexf', '.svg']
app.config['UPLOAD_PATH'] = 'static/uploads'
app.config["SESSION_PERMANENT"] = True
app.config['SESSION_COOKIE_SECURE'] = True

# set up a secret key
app.secret_key = os.getenv("SECRET_KEY")


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
        return render_template('index.html')

    elif request.method == 'POST':

        # get the file uploaded file
        f = request.files['file']
        s_id = request.form['string']

        # add id to session, clear old sessions before starting
        if session.get('id') != None:
            session.clear()
            session['id'] = s_id
        elif session.get("id") == None:
            session['id'] = s_id


        # make directories and add them to the cookies for later
        images_folder = f"static/images/{s_id}"
        directory = os.mkdir(images_folder)


        #file_url =  s_id + ".svg"
        session["file_url"] = "static/svg/visual_" + s_id + ".svg"
        session["zip_url"] = "static/images/" + s_id + ".zip"
       

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


        if file_ext == '.gexf':

            # run plotter - return nothing while it works 
            from plotter import img_plotter
            img_plotter(filename, images_folder, s_id)

            # return nothing
            return jsonify(f'Finishing...')

        elif file_ext == '.svg':

            # get the path for the uploaded file
            uploaded_file = 'static/uploads/' + filename

            # import the svg plotter and run
            from svg_plot import svg_plotter
            svg_plotter(uploaded_file, file_url)

            # return nothing
            return('', 204)


@app.route('/results', methods=['GET'])
def results():
    '''Render a page with the SVG file. Zips the folder for download'''

    import shutil
    s_id = session.get('id')
    name = f"static/images/{s_id}"
    shutil.make_archive(name, 'zip', name)
    return render_template('result.html')


@app.route('/counter', methods=['POST'])
def counter():
    '''Make a counter so the progress is displayed on the screen'''

    # get the global dict counter
    global images_counter

    # look into the dict for the id
    print("DEBUG COUNTER: " + request.data.decode())
    images_processed = images_counter[request.data.decode()]
    result = images_processed.split(" of ")
    completed = result[0]
    total = result[1]

    if completed == total:
        return jsonify('Finished')
    else:
        return jsonify(images_processed)


@app.route("/demo", methods=["GET"])
def demo():
    '''Render a page with the demo SVG file'''

    return render_template("demo.html")
