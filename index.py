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
            #from helpers import img_plotter
            img_plotter(filename, s_id)
            return jsonify("Finished - index")

        elif file_ext == '.svg':
            # import and run svg_plot script
            #from helpers import svg_plotter
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




###############################################
#                                             #
# This part is meant to make the SVG images   #
#                                             #
###############################################

import svgwrite as svg
import xml.etree.ElementTree as et
from PIL import Image
import os, configparser, argparse, sys, platform, traceback
import requests, shutil, re

def img_plotter(filename, s_id):


    print("\n-------------------------\nImage Network Plotter\n-------------------------")

    settings = {'input': 'static/uploads/espacializado.gexf',
                'inimgdir': f'static/uploads/{filename}',
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

    images_folder = f"static/images/{s_id}/img/"
    file_url = f"static/images/{s_id}/img.svg"

    outputfilename = file_url

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

        download_link = "https://i.ytimg.com/vi/" + nodeid + "/hqdefault.jpg?sqp=-oaymwEZCOADEI4CSFXyq4qpAwsIARUAAIhCGAFwAQ"
        response = requests.get(download_link, stream=True)
        imgfile = f"img/{nodeid}.png"

        linkUrl = "https://youtube.com/watch?v=" + nodeid #este link precisará ser substituído pelo nome do arquivo ?

        with open(f'{images_folder}/{nodeid}.png', 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)

            # INFILE

            #infile = os.path.join(settings['inimgdir'], imgfile)  # <<<<<<<<<<<<<<<<<<<<< VERSAO COM DOWNLOAD
            infile = f'{images_folder}/{nodeid}.png'


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
            print("\tPlotting image: ", f'{curimg} of {numimages}')
            progress[s_id] = f"{curimg} of {numimages}"

            link = outsvg.add(outsvg.a(linkUrl,id=nodeid))
            image = link.add(outsvg.image(imgfp, insert=(outnodex, outnodey), size=imgdrawdim))

        outsvg.save(pretty=True)



def svg_plotter(filename, s_id):
    '''plots the video thumbnails on a svg file'''

    output_file = f"static/images/{s_id}/img.svg"

    total = 0
    
    # list to store the lines from the input file
    lista_de_linhas = []

    # open files
    arquivo = open(filename, 'r', encoding='utf8')
    f = open(output_file, 'w')

    # iterate over the file and remove the \n leaving one tag per line
    for linha in arquivo:

        # remove identation
        linha_sem_espaco = linha.lstrip()
        linha_final = ''

        if linha[8:15] == '<circle':
                total += 1

        # remove the \n from the lines inside the tags and append to list
        if linha_sem_espaco[-2] != '>':
            linha_final = linha_sem_espaco.replace('\n',' ')
            lista_de_linhas.append(linha_final)

        # if the line is closing the tag, only append to the list
        else:
            linha_final = linha_sem_espaco
            lista_de_linhas.append(linha_final)

    # Close the file
    arquivo.close()

    # open the output file
    f = open(output_file, 'w')

    # create a counter; if the value is 1 or 2 it will stop the
    #loop from adding data tha's not from a node to the final svg file
    counter = 0
    curimg = 0
    
    # iterate lines - r and cx will be on first, cy and id_class in the second
    # write to the file in the last iteration
    for item in lista_de_linhas:
        if counter == 0:
            if item[0:7] == '<circle':
                r =  re.findall(r'r=".+?"',item)[0][3:-1]
                cx = float(re.findall(r'cx=".+?"',item)[0][4:-1]) - float(r)*1.5
                counter = 1
        if counter == 1:
            if item[23:27] == 'cy="':
                cy = float(re.findall(r'cy=".+?"',item)[0][4:-1]) - float(r)*1.5
                id_class = re.findall(r'class=".+?"',item)[0][10:-1]
                counter = 2
        if counter == 2:
            if item[0:6] == 'stroke':
                f.write(item)
                f.write(f'<a id="{id_class}" target="_blank" xlink:href="https://youtube.com/watch?v={id_class}"><image height="{float(r)*3}" width="{float(r)*3}" x="{cx}" xlink:href="img/{id_class}.png" y="{cy}"/></a>')
                
                images_folder = f"static/images/{s_id}/img"
                download_link = "https://i.ytimg.com/vi/" + id_class + "/hqdefault.jpg?sqp=-oaymwEZCOADEI4CSFXyq4qpAwsIARUAAIhCGAFwAQ"
                response = requests.get(download_link, stream=True)             

                with open(f'{images_folder}/{id_class}.png', 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                
                curimg += 1
                counter = 0

                progress[s_id] = f"{curimg} of {total}"

        # finally writes the line
        f.write(item)

    # close everything and finishes
    f.close()