#!/usr/bin/env python3

import os
# from collections import defaultdict, Counter
import gzip
import argparse
import logging

from freki.readers import tetml, pdfminer
from freki.analyzers import base as basic_analyzer, xycut
from freki.serialize import FrekiBlock, FrekiLine, FrekiDoc

readers = {
    'tetml': tetml.TetmlReader,
    'pdfminer': pdfminer.PdfMinerReader
}
analyzers = {
    'xycut': xycut.XYCutAnalyzer
}

def run(args):
    reader = readers[args.reader](args.infile, debug=args.debug)
    analyzer = analyzers[args.analyzer](debug=args.debug)

    doc_id = _doc_id_from_path(args.infile)
    doc = analyzer.analyze(reader, id=doc_id)

    if args.outfile is None or hasattr(args.outfile, 'write'):
        if args.gzip:
            raise Exception('Cannot gzip to an open stream.')
        process(doc, args.outfile)
    else:
        if args.gzip:
            openfile = gzip.open
            if not args.outfile.endswith('.gz'):
                args.outfile += '.gz'
        else:
            openfile = open
        dirs = os.path.dirname(args.outfile)
        if dirs:
            os.makedirs(dirs, exist_ok=True)
        with openfile(args.outfile, 'wb') as outfile:
            process(doc, outfile)

def process(doc, outfile):
    # Initialize the freki document
    fd = FrekiDoc()
    line_no = 1

    # find minimum left-coordinate if available
    l_margin = [t.llx for p in doc.pages for t in p.tokens]
    l_margin = min(l_margin) if l_margin else 0.0

    for page in doc.pages:
        for blk in page.blocks:
            fb = FrekiBlock(
                doc_id=doc.id,
                page=page.id,
                block_id='{}-{}'.format(page.id, blk.id),
                bbox='{},{},{},{}'.format(blk.llx, blk.lly, blk.urx, blk.ury),
                doc=fd,
                label=blk.label
            )

            for i, line in enumerate(respace(blk, xoffset=(l_margin * -1))):
                fonts = ','.join(
                    sorted(set(['{}-{}'.format(t.font, round(t.height, 1))
                                for t in blk.lines[i].tokens]))
                )
                fl = FrekiLine(
                    line,
                    line=line_no+i,
                    fonts=fonts
                )
                fb.add_line(fl)

            fd.add_block(fb)

            line_no += len(blk.lines)
            #print('\n'.join(respace(blk)))
            # outfile.write(str(fb)+'\n\n')

            # lines = reader.group_lines()
            # respace(lines)
    if outfile is None:
        print(str(fd))
    else:
        outfile.write(str(fd).encode('utf-8'))


# def tabularize(block):
#     # more aggressively try to pigeonhole aligned tokens
#     def approx(n):
#         return round(n/2, 0)
#     tab_indices = sorted(block.tabular_lines())
#     lines = [list(line.tokens) for line in block.lines]
#     colocs = Counter(approx(t.llx) for idx in tab_indices for t in lines[idx])
#     llx_map = {llx: defaultdict(list) for llx in colocs}
#     for i, line in enumerate(lines):
#         if i not in tab_indices:
#             continue
#         cur_llx = 0
#         last_x = 0
#         for tok in line:
#             llx = approx(tok.llx)
#             if colocs[llx] > 1 or (llx - last_x) > (tok.width):
#                 cur_llx = llx  # aligned or has significant space
#             llx_map[cur_llx][i].append(tok)
#             last_x = approx(tok.urx)
#     tablines = defaultdict(list)
#     for _, row_dict in sorted(llx_map.items()):
#         if len(row_dict) == 0:
#             continue
#         toks = [''.join(t.text for t in row_dict.get(i, []))
#                 for i in tab_indices]
#         maxlen = max(len(t) for t in toks)
#         for i, tok in enumerate(toks):
#             tablines[i].append(tok.ljust(maxlen))
#     for i, line in enumerate(lines):
#         if i in tab_indices:
#             yield ' '.join(tablines[i])
#         else:
#             yield ' '.join(t.text for t in line)


def respace(block, xoffset=0.0):
    # -------------------------------------------
    # We want to calculate the average character
    # width for a block. The numerator is the sum of
    # the point widths of the characters
    # -------------------------------------------
    char_num = sum(t.width for line in block.lines for t in line.tokens)

    # -------------------------------------------
    # The denominator is the number of characters
    # in the text in the block.
    # -------------------------------------------
    char_den = 0
    for line in block.lines:
        for t in line.tokens:
            if t.text is not None:
                char_den += len(t.text)

    char_dx = char_num / char_den if char_den > 0 else 0
    min_dx = char_dx / 3
    lines = []
    prev = {}
    for line in block.lines:
        last_x = 0
        cur_line = []
        for t in line.tokens:
            llx = t.llx + xoffset
            if (llx - last_x) < min_dx:
                dx = 0
            elif char_dx == 0:
                dx = 0
            else:
                # dist from last char (at least 1)
                dx = int(((llx - last_x) / char_dx) + 0.5) or 1
            cur_line.append(' ' * dx)
            cur_line.append(t.text if t.text is not None else '')
            last_x = t.urx + xoffset
        lines.append(''.join(cur_line))
        prev = {}
    return lines

def _doc_id_from_path(path):
    bn = os.path.basename(path)
    if bn.endswith('.gz'):
        bn = bn[:-3]
    return os.path.splitext(bn)[0]

def main(arglist=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Find IGTs in text extracted from a PDF",
        epilog='examples:\n'
               '    freki.py --reader tetml --analyzer=xycut in.xml > out.txt'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='count', dest='verbosity', default=2,
        help='increase the verbosity (can be repeated: -vvv)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='show debugging visualizations'
    )
    parser.add_argument(
        '-r', '--reader',
        choices=('tetml', 'pdfminer'), default='tetml'
    )
    parser.add_argument(
        '-a', '--analyzer',
        choices=('xycut'), default='xycut'
    )
    parser.add_argument(
        '-z', '--gzip',
        action='store_true', help='gzip output file'
    )
    parser.add_argument('infile')
    parser.add_argument('outfile')
    args = parser.parse_args(arglist)
    logging.basicConfig(level=50-(args.verbosity*10))
    run(args)

if __name__ == '__main__':
    main()
