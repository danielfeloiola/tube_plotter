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

# Setting the secret key
#app.config['SECRET_KEY'] = os.getenv("KEY")
app.secret_key = 'lksudhfgiuwehrfgsdfyugvjhdskfbvjkdsgfyjhes'
#''.join(random.choice(string.ascii_letters) for i in range(25))

# Configure session to use filesystem (instead of signed cookies)
#app.config['SESSION_FILE_DIR'] = mkdtemp()
#app.config['SESSION_PERMANENT'] = False
#app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SECURE'] = True
#Session(app)

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

            # generate a ramdom string as a session id
            id = get_random_string(12)
            session['id'] = id
            session['type'] = ''

        # render the home page
        return render_template('index.html')


    elif request.method == 'POST':

        # DEBUG:
        #print("FIRST: >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" + session.get('id'))
        #print("SECOND: >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" + session['id'])

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

        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(file_ext)

        # if a graph file is uploaded, also sets up the counter
        if file_ext == '.gexf':

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print("gefx path")
            print(file_ext)

            # set the counter to indicate the analysis started
            images_counter[session.get('id')] = 'Analyzing file'
            session['type'] = 'gexf'

            # run plotter
            #from plotter import img_plotter
            img_plotter('export', filename)

            # return nothing
            return('', 204)

        # if a svg file is uploaded, just get the name and start
        elif file_ext == '.svg':

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print("svg path")
            print(file_ext)

            # get the path for the uploaded file
            uploaded_file = 'static/uploads/' + filename

            # adjust session so it won't count images if svg file is uploaded
            session['type'] = 'svg'
            print("third: >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" + session.get('type'))

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

    # if it's a svg file being analyzed, skip the counter
    print("1: >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" + session.get('type'))
    print("2: >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" + session['type'])



    if session.get('type') == 'svg':
        return jsonify('Finished')


    # get the global dict counter
    global images_counter
    print("3: >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" + session.get('id'))
    id = session.get('id')
    images_processed = images_counter[id]

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
    #return result_str


@app.route("/demo", methods=["GET"])
def demo():
    '''Render a page with the demo SVG file'''

    return render_template("demo.html")









import svgwrite as svg
import xml.etree.ElementTree as et
from PIL import Image
import os, configparser, argparse, sys, platform, traceback
import requests
import shutil

# import the application counter

#from application import images_counter, session

# # TODO:
# fix sys.exit errors > show to the user


def img_plotter(id, filename):


    print("\n-------------------------\nImage Network Plotter\n-------------------------")

    settings = {'input': 'static/uploads/espacializado.gexf',
                'inimgdir': 'static/uploads/espacializado.gexf',
                'copyresized': False,
                'outimgdir': 'img-thumbnail',
                'resizew': 200,
                'resizeh': 200,
                'dispw': 50,
                'disph': 50,
                'restrpage': True,
                'outw': 15000,
                'outh': 15000
               }

    # ------------------------------------------
    # Set internal variables
    #-------------------------------------------

    #outputfilename = os.path.join(os.path.dirname(settings['input']), "visual_" + os.path.basename(str(id)).split(".")[0] + ".svg")
    outputfilename = session["file_url"]
    print(outputfilename)

    imgresizedim = settings['resizew'], settings['resizeh']
    imgdrawdim = settings['dispw'], settings['disph']

    #print("Input file:", settings['input'])
    ingexf = et.parse('static/uploads/' + filename)
    print("Input file:", ingexf)

    # ------------------------------------------
    # Create output dir
    #-------------------------------------------

    if settings['copyresized']:
        if os.path.isabs(settings['outimgdir']):
            outimgdir = settings['outimgdir']
        else:
            outimgdir = os.path.join(os.path.dirname(settings['input']), settings['outimgdir'])
        if not os.path.exists(outimgdir):
            os.makedirs(outimgdir)

    # ------------------------------------------
    # Parse GEXF and generate SVG
    #-------------------------------------------

    try:
        inroot = ingexf.getroot()
        ns = {'gexf' : "http://www.gexf.net/1.3" }
        viz = {'viz' : "http://www.gexf.net/1.3/viz"}
    except Exception as exc:
        print(exc)
        print("**ERROR**\nCould not parse GEXF.")

    typeAttId = -1
    linkAttId = -1
    fileAttId = -1

    graph = inroot.find("gexf:graph", ns)
    if not graph:
        sys.exit("\n**ERROR**\nCould not parse graph file.\n")

    attributes = graph.find(".gexf:attributes",ns)

    for att in attributes:
        if att.get('title') == 'type':
            typeAttId = att.get('id')
        elif att.get('title') == 'link':
            linkAttId = att.get('id')
        elif att.get('title') == 'file':
            fileAttId = att.get('id')

    nodes = graph.find("gexf:nodes", ns)

    # Find graph bounding box and count images
    numnodes = 0

    numimages = 0

    minx = 0
    maxx = 0
    miny = 0
    maxy = 0



    for node in nodes:

        numnodes += 1
        numimages += 1
        try:
            inimgx = float(node.find("viz:position", viz).get('x'))
            inimgy = float(node.find("viz:position", viz).get('y'))
        except AttributeError:
            sys.exit("\n\n**ERROR**\nGraph has not been spatialized. Could not find position data for the nodes\nOpen it in Gephi, apply spatialization algorithm and export to another file.\n")
        except Exception:
            raise
        if inimgx < minx:
            minx = inimgx
        if inimgx > maxx:
            maxx = inimgx
        if inimgy < miny:
            miny = inimgy
        if inimgy > maxy:
            maxy = inimgy

    print("Graph contains", numnodes, "nodes.")
    print("Plotting", numimages, "images.\n")
    print("Minimum X:", minx)
    print("Maximum X:", maxx)
    print("Minimum Y:", miny)
    print("Maximum Y:", maxy)

    # --------
    # Configure output conversion

    inw = maxx - minx
    inh = maxy - miny

    if (inw/inh) >= (settings['outw']/settings['outh']):
        # match width
        outfactor = settings['outw'] / inw
    else:
        # match height
        outfactor = settings['outh'] / inh

    outw = inw * outfactor
    outh = inh * outfactor
    outx = (settings['outw'] - outw)/2
    outy = (settings['outh'] - outh)/2

    # --------
    # Draw output

    outsvg = svg.Drawing(outputfilename, (settings['outw'], settings['outh']), debug=True)

    curimg = 0

    for node in nodes:
        typeAtt = node.find("gexf:attvalues/gexf:attvalue[@for=\'" + str(typeAttId) +"\']",ns)

        curimg += 1

        # add the number of processed images to the variable
        images_counter[session.get('id')] = f'{curimg} of {numimages}'

        innodex = (float(node.find("viz:position", viz).get('x'))-minx)/inw
        innodey = (float(node.find("viz:position", viz).get('y'))-miny)/inh

        if settings['restrpage']:
            outnodex = (innodex * outw) + outx
            outnodey = (innodey * outh) + outy
        else:
            outnodex = innodex
            outnodey = innodey

        nodeid = node.get('id')
        imgfile = "https://i.ytimg.com/vi/" + nodeid + "/hqdefault.jpg?sqp=-oaymwEZCOADEI4CSFXyq4qpAwsIARUAAIhCGAFwAQ"
        linkUrl = "https://youtube.com/watch?v=" + nodeid


        # Adding requests to get the image from the internet
        response = requests.get(imgfile, stream=True)
        with open('img.png', 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)

            infile = "img.png"

            try:
                curimage = Image.open(infile)
            except Exception:
                print("\t**ATTENTION** Image could not be loaded.\n")
                continue

            if settings['copyresized']:
                imgfp = imgfile

                print("\tResizing image...")
                try:
                    curimage.thumbnail(imgresizedim, Image.ANTIALIAS)
                    curimage.save(imgfp)
                except Exception as exc:
                    print("\t**ATTENTION** Problem resizing image.\n")
                    print(exc)
                    continue
            else:

                imgfp = imgfile

            print("\tPlotting image: ", images_counter[session.get('id')])

            link = outsvg.add(outsvg.a(linkUrl,id=nodeid))
            image = link.add(outsvg.image(imgfp, insert=(outnodex, outnodey), size=imgdrawdim))

        outsvg.save(pretty=True)
