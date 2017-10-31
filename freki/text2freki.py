from freki.serialize import FrekiDoc, FrekiBlock, FrekiLine
import codecs
import re
import chardet
import logging
import argparse


def run(args):
    frek = read_and_convert(args.infile, args.igtfile, args.encoding, args.detect)
    out = open(args.outfile, 'w', encoding='utf8')
    out.write(str(frek))


def convert_text(doc_id, text, span_text=None):
    """
    Convert a string to freki
    :param doc_id: name of document
    :param text: text of document
    :param span_text: text identifying IGT spans, if available
    :return: freki object
    """
    w_index = 1
    wo_index = 1
    pre2post = {}
    for line in re.split('\r\n|\n', text):
        if not re.match('^\s*$', line):
            pre2post[w_index] = wo_index
            wo_index += 1
        w_index += 1
    line_dict = {}
    s_index = 0
    if span_text:
        for line in span_text.split('\n'):
            if len(line):
                parts = line.split()
                tags = parts[2:]
                start = int(parts[0])
                for i in range(start, int(parts[1]) + 1):
                    try:
                        num = pre2post[i]
                    except KeyError:
                        print("Warning: a line specified in the igt file is a blank line in the document. "
                         "Check the line numbers in the igt file. Skipping the problem line.")
                        break
                    line_dict[num] = (tags[num - start], 's' + str(s_index))
            s_index += 1
    frek = FrekiDoc()
    text = re.sub(r'(\r\n|\n){2,}', '\n\n', text)
    blocks = re.split('\n\n', text)
    index = 1
    b_index = 1
    for para in blocks:
        lines = re.split('\r\n|\n', para)
        linenos = []
        for line in lines:
            f_line = FrekiLine(line)
            f_line.attrs['line'] = index
            f_line.attrs['bbox'] = '0,0,0,0'
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


def read_and_convert(path, igt_path=None, encoding='utf-8', detect_encoding=False):
    """
    Read in a text file and convert it to freki. igt_path file format: startline endline tag1 tag2 ... tagN\n
    :param path: path to the text file
    :param igt_path: path to the text file containing IGT span info
    :param encoding: name of the encoding of the file
    :param detect_encoding: setting to true will first detect an encoding rather than using the default.
    :return: freki object
    """
    name = path.split('/')[-1].split('.')[0]
    igt_text = None
    if detect_encoding:
        bytes = open(path, 'rb').read()
        p_predict = chardet.detect(bytes)
        text = codecs.open(path, encoding=p_predict['encoding'], errors='strict').read()
        if igt_path:
            i_predict = chardet.detect(open(igt_path, 'rb').read())
            igt_text = codecs.open(igt_path, encoding=i_predict['encoding']).read()
        logging.info('Using encoding: ' + p_predict['encoding'])
        logging.info('Encoding detection uses the Chardet library: https://pypi.python.org/pypi/chardet')
    else:
        try:
            text = codecs.open(path, encoding=encoding, errors='strict').read()
            if igt_path:
                igt_text = codecs.open(igt_path, encoding=encoding).read()
        except UnicodeDecodeError:
            bytes = open(path, 'rb').read()
            p_predict = chardet.detect(bytes)
            text = codecs.open(path, encoding=p_predict['encoding'], errors='strict').read()
            if igt_path:
                i_predict = chardet.detect(open(igt_path, 'rb').read())
                igt_text = codecs.open(igt_path, encoding=i_predict['encoding']).read()
            logging.info('The file cannot be read using encoding ' + encoding + '. Instead using ' + p_predict['encoding'])
            logging.info('Encoding detection uses the Chardet library: https://pypi.python.org/pypi/chardet\n')
            logging.info("If encoding " + p_predict['encoding'] + ' is not correct please specify the encoding as an argument')
            logging.info('For a detailed list of encodings available in Python visit https://docs.python.org/2.4/lib/standard-encodings.html')
        except LookupError:
            print('Unknown encoding. If you want the system to automatically detect an encoding set detect_encoding=True')
            print('For a detailed list of encodings available in Python visit https://docs.python.org/2.4/lib/standard-encodings.html')
            raise
    frek = convert_text(name, text, igt_text)
    return frek


def main(arglist=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Convert a plain text file to Freki format",
        prog='text-to-freki',
        epilog='examples:\n'
               '    text-to-freki in.txt out.freki --igtfile=igts.txt --detect-encoding=true'
    )
    parser.add_argument('infile', help='plain text file')
    parser.add_argument('outfile', help='path to freki output file')
    parser.add_argument('--igtfile', help='plain text file containing igt span info')
    parser.add_argument('--encoding', default='utf-8', help='encoding of the input file')
    parser.add_argument(
        '-d', '--detect-encoding', dest='detect', default=False, help='automatically detects encoding when set to true'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='count', dest='verbosity', default=2,
        help='increase the verbosity (can be repeated: -vvv)'
    )
    args = parser.parse_args(arglist)
    logging.basicConfig(level=50-(args.verbosity*10))
    run(args)


if __name__ == '__main__':
    main()