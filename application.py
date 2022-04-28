# important stuff
from flask import Flask, jsonify, render_template, session, request
import os #, string

# SQLAlchemy for the database LOL
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# > Getting the DB ready
# Check for db url variable
uri = os.getenv("DATABASE_URL")
if not uri:
    raise RuntimeError("DATABASE_URL is not set")

# damm you heroku
if uri.startswith("postgres://"):     
    uri = uri.replace("postgres://", "postgresql://", 1)

# And set up database
engine = create_engine(uri)
db = scoped_session(sessionmaker(autocommit=False,
                                 autoflush=False,
                                 bind=engine))

Base = declarative_base()
Base.query = db.query_property()

# class for the database
class Progress(Base):
    __tablename__ = 'progress_table'
    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True,)
    progress = Column(Integer)
    total = Column(Integer)

Base.metadata.create_all(bind=engine)


# dict to count images
images_counter = dict()


# Configure application
app = Flask(__name__)

# Uploads settings
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

        # add id to the session
        session['id'] = s_id

        # add to the db
        #progress = Progress(session_id=f"{s_id}", progress=0, total=0)
        #db.add(progress)
        #db.commit()

        # make directories and add them to the cookies for later
        images_folder = f"static/images/{s_id}"
        directory = os.mkdir(images_folder)


        file_url =  s_id + ".svg"
        session["file_url"] = "static/svg/visual_" + s_id + ".svg"
        session["zip_url"] = "static/images/" + s_id + ".zip"

        print("URLS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(session["file_url"])
        print(session["zip_url"])

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
            img_plotter(filename, images_folder, file_url, s_id)

            # return nothing
            return jsonify(f'Finishing...')# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

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
    name = f"static/images/{session['id']}"
    shutil.make_archive(name, 'zip', name)

    return render_template('result.html')


@app.route('/counter', methods=['POST'])
def counter():
    '''Make a counter so the progress is displayed on the screen'''

    #progress = db.query(Progress).filter(Progress.session_id==request.data.decode()).first()
    



    # get the global dict counter
    global images_counter

   
    # if uploading a gexf, do the counting
    #else:

    # look into the dict for the id
    images_processed = images_counter[request.data.decode()]
    result = images_processed.split(" of ")
    completed = result[0]
    total = result[1]

    # if completed return finished to display the results
    if completed == total:
        return jsonify('Finished')

    else:
        return jsonify(images_processed)

        
  
    # print("DEBUG - PROGRESS & TOTAL VAR: " + str(progress.progress) + " of " + str(progress.total) + " from " + request.data.decode())

  

    # if completed return finished to display the results
    #if progress.progress == progress.total and progress.total != 0:
    #    return jsonify('Finished')
    #
    #else:
    #    return jsonify(f"{progress.progress} of {progress.total}")


@app.route("/demo", methods=["GET"])
def demo():
    '''Render a page with the demo SVG file'''

    return render_template("demo.html")
