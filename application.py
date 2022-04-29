# important stuff
from flask import Flask, jsonify, render_template, session, request
from flask_session import Session
import os, shutil, bmemcached

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

# memcAache setup
servers = os.environ.get('MEMCACHIER_SERVERS', '').split(',')
user = os.environ.get('MEMCACHIER_USERNAME', '')
passw = os.environ.get('MEMCACHIER_PASSWORD', '')
mc = bmemcached.Client(servers, username=user, password=passw)
mc.enable_retry_delay(True)  # Enabled by default. Sets retry delay to 5s.





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

        # get an id from de front-end to keed track of progress
        s_id = request.form['string']

        # make directories and set up the session for later
        images_folder = f"static/images/{s_id}"
        directory = os.mkdir(images_folder)
        session["id"] = s_id
        session["file_url"] = "static/svg/visual_" + s_id + ".svg"
        session["zip_url"] = "static/images/" + s_id + ".zip"
       
        # check filename and extension
        filename = f.filename
        if filename == '':
            return jsonify('Check filename')
        else:
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                return jsonify('Please check file extension')
            f.save(os.path.join(app.config['UPLOAD_PATH'], filename))


        if file_ext == '.gexf':
            # run plotter script and return Finished to show the link to results page 
            from plotter import img_plotter
            img_plotter(filename, images_folder, s_id)
            return jsonify("Finished")

        elif file_ext == '.svg':
            # import and run svg_plot script
            from svg_plot import svg_plotter
            svg_plotter(f'static/uploads/{filename}', file_url)
            return jsonify("Finished")


@app.route('/results', methods=['GET'])
def results():
    '''Render a page with the SVG file. Zips the folder for download'''

    name = f"static/images/{session.get('id')}"
    shutil.make_archive(name, 'zip', name)
    return render_template('result.html')


@app.route('/counter', methods=['POST'])
def counter():
    '''Make a counter so the progress is displayed on the screen'''

    result = mc.get(request.data.decode()).split(" of ")
    completed = result[0]
    total = result[1]   

    if completed != total:
        return jsonify(f"{completed} of {total}")
    else:
        return jsonify("Finished")


@app.route("/demo", methods=["GET"])
def demo():
    '''Render a page with the demo SVG file'''

    return render_template("demo.html")






