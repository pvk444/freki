#!/usr/bin/env python

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
    for page in reader.pages():
        for blk in reader.blocks(page):
            print(
                'doc_id={} block_id={} bbox={},{},{},{} {} {}'.format(
                    doc_id,
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
            for i, line in enumerate(respace(blk)):
                print('line={}:{}'.format(line_no+i, line))
            line_no += len(blk.lines)
            #print('\n'.join(respace(blk)))
            print()

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


def respace(block):
    l_margin = min(t.llx for line in block.lines for t in line.tokens)
    char_dx = (
        sum(t.width for line in block.lines for t in line.tokens)
        / float(sum(len(t.text) for line in block.lines for t in line.tokens))
    )
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
            else:
                # dist from last char (at least 1)
                dx = int(((llx - last_x) / char_dx) + 0.5) or 1
            cur_line.append(' ' * dx)
            cur_line.append(t.text)
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
    parser.add_argument('infile')
    parser.add_argument(
        '-f', '--format',
        choices=('tetml','pdfminer'), default='tetml'
    )
    args = parser.parse_args(arglist)
    logging.basicConfig(level=50-(args.verbosity*10))
    run(args)

if __name__ == '__main__':
    main()
