#!/usr/bin/env python3

import os
# from collections import defaultdict, Counter
import gzip
import argparse
import logging

from freki.readers import tetml, pdfminer
from freki.analyzers import base as basic_analyzer, xycut
from freki.serialize import FrekiBlock, FrekiLine, FrekiDoc

INTERLINEAR_THRESHOLD = 0.6

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

    logging.info('Analyzing {}'.format(args.infile))
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

            for i, data in enumerate(respace(blk, xoffset=(l_margin * -1))):
                line, iscore = data
                fonts = ','.join(
                    sorted(set(['{}-{}'.format(t.font, round(t.height, 1))
                                for t in blk.lines[i].tokens]))
                )
                bbox = blk.lines[i].bbox
                fl = FrekiLine(
                    line,
                    line=line_no+i,
                    fonts=fonts,
                    bbox='{0.llx},{0.lly},{0.urx},{0.ury}'.format(bbox),
                    iscore=None if iscore is None else '{:.2f}'.format(iscore)
                )
                fb.add_line(fl)

            fd.add_block(fb)

            line_no += len(blk.lines)
    if outfile is None:
        print(str(fd))
    else:
        outfile.write(str(fd).encode('utf-8'))


def _llx_col(x, dx):
    if dx == 0:
        dx = 1  # avoid division by zero
    return int((x/dx) + 0.5)


def _interlinear_score(toklist, prev):
    a_llxs = [t[0] for t in toklist]
    left = min(a_llxs)
    b_llxs = set(c for c, _ in prev if c >= left)
    if len(a_llxs) > len(b_llxs):
        a_llxs, b_llxs = b_llxs, a_llxs
    return sum(1 if c in b_llxs else 0 for c in a_llxs) / float(len(b_llxs))


def _columnized_tokens(tokens, min_dx, char_dx, xoffset):
    last_x = 0
    toklist = []
    for t in tokens:
        dx = t.llx - last_x
        text = t.text or ''
        # this doesn't belong here, but it's currently the last time we
        # have the token feature data available with the text
        if t.features.get('sup') == True:
            text = '^{{{}}}'.format(text)
        elif t.features.get('sub') == True:
            text = '_{{{}}}'.format(text)
        # rejoin tokens not separated by spaces
        # print(text, char_dx, dx, min_dx)
        if not toklist or (char_dx > 0 and dx >= min_dx):
            col = _llx_col(t.llx + xoffset, char_dx)
            toklist.append([col, text])
        else:
            toklist[-1][1] += text
        last_x = t.urx
    return toklist


def _respace_group(group):
    cols = {}  # column : [ rowidx, ... ]
    colidx = {}  # rowidx : colidx
    nextcol = {}  # rowidx : column
    for i, data in enumerate(group):
        toklist, iscore = data
        for col, text in toklist:
            cols[col] = cols.get(col, []) + [i]
        colidx[i] = 0
        nextcol[i] = 0

    for col, rowidxs in sorted(cols.items()):
        start = max(col, max(nextcol[i] for i in rowidxs))
        for i in rowidxs:
            tok = group[i][0][colidx[i]]
            tok[0] = start
            nextcol[i] = start + len(tok[1]) + 1
            colidx[i] += 1


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

    char_dx = char_num / char_den if char_den > 0 else 1.0
    min_dx = char_dx / 3

    groups = []
    toklists = []
    prev = None
    for line in block.lines:
        toklist = _columnized_tokens(line.tokens, min_dx, char_dx, xoffset)
        iscore = _interlinear_score(toklist, prev) if prev else None
        if iscore is None or iscore < INTERLINEAR_THRESHOLD:
            groups.append([(toklist, iscore)])
        else:
            groups[-1].append((toklist, iscore))
        prev = toklist
    
    lines = []
    for group in groups:
        _respace_group(group)
        for toklist, iscore in group:
            lastcol = 0
            toks = []
            for col, text in toklist:
                toks.append(' ' * (col - lastcol))
                toks.append(text)
                lastcol += (col - lastcol) + len(text)
            lines.append((''.join(toks), iscore))
    return lines


def _doc_id_from_path(path):
    bn = os.path.basename(path)
    if bn.endswith('.gz'):
        bn = bn[:-3]
    return os.path.splitext(bn)[0]


def main(arglist=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Analyze the document structure of text in a PDF",
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
        choices=(['xycut']), default='xycut'
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
