from freki.serialize import FrekiDoc, FrekiBlock, FrekiLine
import codecs
import re


def convert_text(doc_id, text, span_text=None):
    """
    Convert a text file to freki
    :param doc_id: name of document
    :param text: text of document
    :param span_text: text identifying IGT spans, if available
    :return: freki object
    """
    line_dict = {}
    s_index = 0
    if span_text:
        for line in span_text.split('\n'):
            parts = line.split()
            tags = parts[2:]
            start = int(parts[0])
            for i in range(start, int(parts[1]) + 1):
                line_dict[i] = (tags[i - start], 's' + str(s_index))
            s_index += 1
    frek = FrekiDoc()
    text = re.sub('\n\n+', '\n\n', text)
    blocks = re.split('\n\n', text)
    index = 1
    b_index = 1
    for para in blocks:
        lines = para.split('\n')
        linenos = []
        for line in lines:
            f_line = FrekiLine(line)
            f_line.attrs['line'] = index
            linenos.append(index)
            if index in line_dict:
                f_line.attrs['tag'] = line_dict[index][0]
                f_line.attrs['span_id'] = line_dict[index][1]
            frek.add_line(f_line)
            index += 1
        block = FrekiBlock(linenos, linenos[0], linenos[-1], frek)
        block._attrs['page'] = '1'
        block._attrs['block_id'] = 'b' + str(b_index)
        block._attrs['doc_id'] = doc_id
        b_index += 1
        frek.add_block(block)
    return frek


def read_text(path, igt_path=None):
    """
    Read in a text file and convert it to freki
    :param path: path to the text file
    :param igt_path: path to the text file containing IGT span info

    igt_path file format: startline endline tag1 tag2 ... tagN \n
    """
    name = path.split('/')[-1].split('.')[0]
    text = open(path, 'r').read()
    igt_text = None
    if igt_path:
        igt_text = open(igt_path, 'r').read()
    frek = convert_text(name, text, igt_text)
    return frek