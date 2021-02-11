# add thumbnails to a svg file


def svg_plotter(file, output_file):
    '''plots the video thumbnails on a svg file'''

    # Needed to find the substrings
    # necessario para encontrar substrings
    import re

    # list to store the lines from the input file
    # lista que armazena as linhas do arquivo de entrada
    lista_de_linhas = []

    # open original file
    # abre o arquivo original
    arquivo = open(file, 'r', encoding='utf8')

    # iterate over the file and remove the \n leavong one tag per line
    # itera pelo arquivo original e remove o \n para deixar uma tag por linha
    for linha in arquivo:

        # remove identation
        # remove identacao
        linha_sem_espaco = linha.lstrip()
        linha_final = ''

        # remove the \n from the lines inside the tags and append to list
        # remove o \n de dentro das tags e anexa a lista
        if linha_sem_espaco[-2] != '>':
            linha_final = linha_sem_espaco.replace('\n',' ')
            lista_de_linhas.append(linha_final)

        # if the line is closing the tag, only append to the list
        # quando nao ha o \n apenas anexa a linah a lista
        else:
            linha_final = linha_sem_espaco
            lista_de_linhas.append(linha_final)

    # Close the file
    # fecha o arquivo
    arquivo.close()


    # open the output file
    # abre o arquivo de saida
    f = open(output_file, 'w')

    # create a counter; if the value is 1 or 2 it will stop the
    #loop from adding data tha's not from a node to the final svg file
    #
    # cria um contador; se o valor for 1 ou 2 impede o loop de adicionar
    # dados que nao sao de nodes no arquivo final
    counter = 0

    for item in lista_de_linhas:

        # look only for the nodes
        # encontra os nos
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

                # if we re on the last line of the tag, then also add the img tag
                # then resets counter for the next tag and skip to the next iteration
                # se for a ultima linha da tag, tambem adiciona a imagem
                # e reseta o contador para a proxima tag e pula para a proxima iteracao
                f.write(item)
                f.write(f'<a id="{id_class}" target="_blank" xlink:href="https://youtube.com/watch?v={id_class}"><image height="{float(r)*3}" width="{float(r)*3}" x="{cx}" xlink:href="https://i.ytimg.com/vi/{id_class}/hqdefault.jpg?sqp=-oaymwEZCOADEI4CSFXyq4qpAwsIARUAAIhCGAFwAQ" y="{cy}"/></a>')

                counter = 0
                continue

        # finally writes the line
        # por ultimo, escreve a linha no arquivo
        f.write(item)

    # close everything and finishes
    # fecha o arquivo e termina
    f.close()


if __name__ == "__main__":
    svg_plotter()
