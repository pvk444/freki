#!/usr/bin/env python3
import os
from os import path
from collections import defaultdict, Counter
import argparse
import logging

from readers import tetml, pdfminer

readers = {
    'tetml': tetml.TetmlReader,
    'pdfminer': pdfminer.PdfMinerReader
}

def run(args):
    reader = readers[args.format](args.infile)
    doc_id = path.splitext(path.basename(args.infile))[0]
    line_no = 1
    os.makedirs(os.path.dirname(args.outfile), exist_ok=True)
    outfile = open(args.outfile, 'w', encoding='utf-8')
    for page in reader.pages():
        for blk in reader.blocks(page):
            outfile.write(
                'doc_id={} page={} block_id={} bbox={},{},{},{} {} {}\n'.format(
                    doc_id,
                    page.id,
                    blk.id,
                    blk.llx,
                    blk.lly,
                    blk.urx,
                    blk.ury,
                    line_no,
                    line_no + len(blk.lines) - 1
                )
            )
            # if blk.tabular:
            #     print('<respaced>')
            #     print('\n'.join(respace(blk)))
            #     print('</respaced>\n\n<tabularized>')
            #     print('\n'.join(tabularize(blk)))
            #     print('</tabularized>')
            # else:
            for i, line in enumerate(respace(blk, args.deindent_blocks)):
                fonts = ','.join(sorted(set(['{}-{}'.format(t.font, t.size) for t in blk.lines[i].tokens])))
                outfile.write('line={} fonts={}:{}\n'.format(line_no+i, fonts, line))
            line_no += len(blk.lines)
            #print('\n'.join(respace(blk)))
            outfile.write('\n')

        # lines = reader.group_lines()
        # respace(lines)

def tabularize(block):
    # more aggressively try to pigeonhole aligned tokens
    def approx(n):
        return round(n/2, 0)
    tab_indices = sorted(block.tabular_lines())
    lines = [list(line.tokens) for line in block.lines]
    colocs = Counter(approx(t.llx) for idx in tab_indices for t in lines[idx])
    llx_map = {llx: defaultdict(list) for llx in colocs}
    for i, line in enumerate(lines):
        if i not in tab_indices:
            continue
        cur_llx = 0
        last_x = 0
        for tok in line:
            llx = approx(tok.llx)
            if colocs[llx] > 1 or (llx - last_x) > (tok.width):
                cur_llx = llx  # aligned or has significant space
            llx_map[cur_llx][i].append(tok)
            last_x = approx(tok.urx)
    tablines = defaultdict(list)
    for _, row_dict in sorted(llx_map.items()):
        if len(row_dict) == 0:
            continue
        toks = [''.join(t.text for t in row_dict.get(i, []))
                for i in tab_indices]
        maxlen = max(len(t) for t in toks)
        for i, tok in enumerate(toks):
            tablines[i].append(tok.ljust(maxlen))
    for i, line in enumerate(lines):
        if i in tab_indices:
            yield ' '.join(tablines[i])
        else:
            yield ' '.join(t.text for t in line)


def respace(block, deindent=False):
    t = list((t.llx for line in block.lines for t in line.tokens))
    l_margin = min(t) if (deindent and t) else 0

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
            llx = t.llx - l_margin
            if (llx - last_x) < min_dx:
                dx = 0
            elif char_dx == 0:
                dx = 0
            else:
                # dist from last char (at least 1)
                dx = int(((llx - last_x) / char_dx) + 0.5) or 1
            cur_line.append(' ' * dx)
            cur_line.append(t.text if t.text is not None else '')
            last_x = t.urx - l_margin
        lines.append(''.join(cur_line))
        prev = {}
    return lines

def main(arglist=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Find IGTs in text extracted from a PDF",
        epilog='examples:\n'
            '    freki.py --format tetml infile.xml > outfile.txt'
    )
    parser.add_argument('-v', '--verbose',
        action='count', dest='verbosity', default=2,
        help='increase the verbosity (can be repeated: -vvv)'
    )
    parser.add_argument(
        '-f', '--format',
        choices=('tetml','pdfminer'), default='tetml'
    )
    parser.add_argument('--deindent-blocks',
        action='store_true',
        help='remove consistent leading space in block lines'
    )
    parser.add_argument('infile')
    parser.add_argument('outfile')
    args = parser.parse_args(arglist)
    logging.basicConfig(level=50-(args.verbosity*10))
    run(args)

if __name__ == '__main__':
    main()
