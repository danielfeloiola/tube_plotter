# important stuff
from flask import Flask, jsonify, render_template, session, request
from flask_session import Session
import os

import shutil

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

        # get an id
        s_id = request.form['string']
        session['id'] = s_id

        # add id to session, clear old sessions before starting
        #if session.get('id') != None:
        #    session.clear()
        #    session['id'] = s_id
        #elif session.get("id") == None:
        #    session['id'] = s_id

        # make directories and add them to the session for later
        images_folder = f"static/images/{s_id}"
        directory = os.mkdir(images_folder)
        session["file_url"] = "static/svg/visual_" + s_id + ".svg"
        session["zip_url"] = "static/images/" + s_id + ".zip"
        
        #file_url =  s_id + ".svg"
        #session["counter"] = "0 of 0"
        #print("<<<<____DEBUG SESSION COUNTER_____>>>>")
        #print(session.get("counter"))

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

            # run plotter - return nothing while it works 
            #from plotter import img_plotter
            img_plotter(filename, images_folder, session.get("id"))

            # return Finished to show the link to results page 
            return jsonify("Finished")

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

    name = f"static/images/{session.get('id')}"
    shutil.make_archive(name, 'zip', name)
    return render_template('result.html')


@app.route('/counter', methods=['POST'])
def counter():
    '''Make a counter so the progress is displayed on the screen'''

    result = images_counter[request.data.decode()].split(" of ")
    completed = result[0]
    total = result[1]

    if completed != total:
        return jsonify(f"{completed} of {total}")

@app.route("/demo", methods=["GET"])
def demo():
    '''Render a page with the demo SVG file'''

    return render_template("demo.html")














import svgwrite as svg
import xml.etree.ElementTree as et
from PIL import Image
import os#, configparser, argparse, sys, platform, traceback
import requests
#import shutil

# import the application counter
#from application import session #, images_counter


def img_plotter(filename, images_folder, s_id):


    print("DEBUG IMG_PLOTTER: " + session.get('id'))

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

    outputfilename = session["file_url"]
    #outputfilename = file_url ## <<<<<<<<<<<<<<<

    imgresizedim = settings['resizew'], settings['resizeh']
    imgdrawdim = settings['dispw'], settings['disph']

    # ARQUIVO GEXF DE ENTRADA
    ingexf = et.parse('static/uploads/' + filename)


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
        
        # Update progress
        curimg += 1

        # add the number of processed images to the variable
        #global images_counter
        images_counter[session.get("id")] = f"{curimg} of {numimages}"
        #session['counter'] = f'{curimg} of {numimages}'

        typeAtt = node.find("gexf:attvalues/gexf:attvalue[@for=\'" + str(typeAttId) +"\']",ns)

        innodex = (float(node.find("viz:position", viz).get('x'))-minx)/inw
        innodey = (float(node.find("viz:position", viz).get('y'))-miny)/inh

        if settings['restrpage']:
            outnodex = (innodex * outw) + outx
            outnodey = (innodey * outh) + outy
        else:
            outnodex = innodex
            outnodey = innodey

        nodeid = node.get('id')

        # TODO: O SVG AINDA ESTA VINDO COM OS LINKS E NAO COM OS ARQUIVOS <<<<<
        imgfile = "https://i.ytimg.com/vi/" + nodeid + "/hqdefault.jpg?sqp=-oaymwEZCOADEI4CSFXyq4qpAwsIARUAAIhCGAFwAQ"
        linkUrl = "https://youtube.com/watch?v=" + nodeid #este link precisará ser substituído pelo nome do arquivo ?

        '''
        imgfile = node.find("gexf:attvalues/gexf:attvalue[@for=\'" + str(fileAttId) +"\']",ns).get('value')
        linkUrl = node.find("gexf:attvalues/gexf:attvalue[@for=\'" + str(linkAttId) +"\']",ns).get('value')
        print("\tImage file:", imgfile)
        infile = os.path.join(settings['inimgdir'], imgfile)
        '''


        # Adding requests to get the image from the internet
        response = requests.get(imgfile, stream=True)


        with open(f'{images_folder}/{nodeid}.png', 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)

            # INFILE
            infile = f'{images_folder}/{nodeid}.png'
            # infile = "img.png" # alterando: cada imagem tera o nome do nodeid

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

            # DECOMMENT after debug #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            #print("\tPlotting image: ", f'{curimg} of {numimages}')

            link = outsvg.add(outsvg.a(linkUrl,id=nodeid))
            image = link.add(outsvg.image(imgfp, insert=(outnodex, outnodey), size=imgdrawdim))

        outsvg.save(pretty=True)

