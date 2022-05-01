# add thumbnails to a svg file
from application import mc
import bmemcached, re


def svg_plotter(filename, s_id):
    '''plots the video thumbnails on a svg file'''

    output_file = f"static/images/{s_id}/img.svg"
    links = False
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
                f.write(f'<a id="{id_class}" target="_blank" xlink:href="https://youtube.com/watch?v={id_class}"><image height="{float(r)*3}" width="{float(r)*3}" x="{cx}" xlink:href="https://i.ytimg.com/vi/{id_class}/hqdefault.jpg?sqp=-oaymwEZCOADEI4CSFXyq4qpAwsIARUAAIhCGAFwAQ" y="{cy}"/></a>')
                curimg += 1
                counter = 0
                mc.set(s_id, f"{curimg} of {total}")


        # finally writes the line
        f.write(item)

    # close everything and finishes
    f.close()


if __name__ == "__main__":
    svg_plotter()

