# IMAGE PLOTTER
# Basen on Mintz's image-network plotter
# https://github.com/amintz/image-network-plotter
# Adapted by Daniel Loiola (2020)


import svgwrite as svg
import xml.etree.ElementTree as et
from PIL import Image
import os, configparser, argparse, sys, platform, traceback
import requests
import shutil

# import the application counter
from application import images_counter, session


def img_plotter(filename, images_folder):


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

    #print(outputfilename)

    imgresizedim = settings['resizew'], settings['resizeh']
    imgdrawdim = settings['dispw'], settings['disph']

    #print("Input file:", settings['input'])

    #ARQUIVO GEXF DE ENTRADA  <<<<<
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


       
    

        # Trying to save img to a different place ###########################
        with open(f'{images_folder}/{nodeid}.png', 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)

            # INFILE
            #infile = nodeid + '.png'
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

            print("\tPlotting image: ", images_counter[session.get('id')])

            link = outsvg.add(outsvg.a(linkUrl,id=nodeid))
            image = link.add(outsvg.image(imgfp, insert=(outnodex, outnodey), size=imgdrawdim))

        outsvg.save(pretty=True)

if __name__ == "__main__":
    img_plotter()
