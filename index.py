# important stuff
from flask import Flask, jsonify, render_template, request #session
import os, shutil

# Configure application
app = Flask(__name__)

# settings
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.gexf', '.svg']
app.config['UPLOAD_PATH'] = 'static/uploads'

# set up a secret key
app.secret_key = os.getenv("SECRET_KEY")

# store progress -> not ideal but...
progress = dict()

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

        # Making a dir to save images
        s_id = request.form['string']
        os.makedirs(f"static/images/{s_id}/img/")

        # get the file uploaded file and check name and ext
        f = request.files['file']
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
            from helpers import img_plotter
            img_plotter(filename, s_id)
            return jsonify("Finished - index")

        elif file_ext == '.svg':
            # import and run svg_plot script
            from helpers import svg_plotter
            svg_plotter(f'static/uploads/{filename}', s_id)
            return jsonify("Finished")


@app.route('/results/<sid>', methods=['GET'])
def results(sid):
    '''Render a page with the SVG file. Zips the folder for download'''

    file_url = f"images/{sid}/img.svg"
    zip_url = f"images/{sid}/img.zip"
    shutil.make_archive(f"static/images/{sid}/img", 'zip', f"static/images/{sid}/img")

    return render_template('result.html', zip_url=zip_url, file_url=file_url)


@app.route('/counter', methods=['POST'])
def counter():
    '''Make a counter so the progress is displayed on the screen'''

    s_id = request.data.decode()
    result = progress[s_id].split(" of ")
    
    completed = result[0]
    total = result[1]   

    if completed != total:
        return jsonify(f"{completed} of {total}")
    else:
        return jsonify("Finished - counter")



@app.route("/demo", methods=["GET"])
def demo():
    '''Render a page with the demo SVG file'''

    return render_template("demo.html")


