
from collections import defaultdict, Counter
from itertools import groupby
import logging

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from freki.structures import Line, Block

min_line_overlap = 0.01


class FrekiReader(object):

    def __init__(self, debug=False):
        self._lines = {}
        self._debug = debug

    def _line_dy(self):
        all_line_diffs = []
        for page in self.pages():
            lines = self.lines(page)
            line_diffs = [a.ury - b.lly for a, b in zip(lines[:-1], lines[1:])]
            all_line_diffs.extend(line_diffs)

        if not all_line_diffs:
            line_dy = 0
        elif len(all_line_diffs) == 1:
            line_dy = all_line_diffs[0]
        else:
            # Get the average line diff.
            # line_dy = statistics.mean(line_diffs)
            line_dy = Counter(all_line_diffs).most_common(1)[0][0]
            # line_dy = max(line_diffs)
            # line_dy = statistics.variance(line_diffs) - statistics.stdev(line_diffs)

        return line_dy

    def pages(self, *page_ids):
        '''
        Return the Page objects for the document.
        Zero or more *page_ids* may be specified, which are the page
        numbers (e.g. `1` is the first page). If zero *page_ids* are
        given, all pages are returned in order.
        '''
        raise NotImplementedError()

    def blocks(self, page, coefficient=1.0):
        lines = self.lines(page)
        line_dy = coefficient * self._line_dy()
        i = 1

        block = Block(id='{}-{}'.format(page.id, i))
        if lines:
            last_y = lines[0].lly
            for line in lines:
                if ((last_y - line.ury > line_dy or last_y - line.ury < 0)
                        and block.lines):
                    yield block
                    i += 1
                    block = Block(id='{}-{}'.format(page.id, i))
                block.append(line)
                last_y = line.lly

        # If we still have an unreturned block...
        if block.lines:
            yield block

    def lines(self, page):
        if page.id not in self._lines:
            lines = []
            for llx, lly, urx, ury in _zones(page, debug=self._debug):

                baselines = defaultdict(Line)
                for token in page.tokens:
                    if (token.llx >= llx and
                            token.lly >= lly and
                            token.urx <= urx and
                            token.ury <= ury):
                        baselines[token.lly].append(token)

                if not baselines:
                    continue

                baselines = merge_lines(list(baselines.values()))
                baselines.sort(key=lambda line: line.lly, reverse=True)

                for line in baselines:
                    line.sort()  # sort the tokens in each line
                    lines.append(line)

            # and sort the lines in each page
            # lines = sorted(lines, key=lambda line: line.lly, reverse=True)
            self._lines[page.id] = lines

        return self._lines[page.id]

def _zones(page, debug=False):
    if not page.tokens:
        return

    w, h = int(page.page_width), int(page.page_height)
    bitmap = np.zeros((h, w))

    ch = []  # token heights as a heuristic for minimum gap
    for token in page.tokens:
        llx, lly = int(token.llx), int(token.lly)
        urx, ury = int(token.urx), int(token.ury)
        ch.append(token.height)
        bitmap[lly:ury, llx:urx] = token.height

    # debugging
    ax=None
    if debug:
        fig, ax = plt.subplots()
        ax.imshow(bitmap, origin='lower')
        ax.autoscale(False)

    min_gap = sum(ch) / len(ch)
    min_ratios = (1/4, 1/16)  # (vert, horiz) don't cut smaller than this
    for llx, lly, urx, ury in _find_zones(
            bitmap, 0, 0, w, h, min_gap, min_ratios, ax=ax):

        logging.debug(
            'Page {} zone: llx: {}\tlly: {}\turx: {}\tury: {}'
            .format(page.id, llx, lly, urx, ury)
        )
        if ax is not None:
            ax.add_patch(
                Rectangle((llx, lly), (urx-llx), (ury-lly),
                          edgecolor='w', facecolor='none')
            )

        yield llx, lly, urx, ury

    if debug:
        plt.show()


def _find_zones(bitmap, llx, lly, urx, ury, min_gap, min_ratios, thresh=0, ax=None):
    """
    This is a modified implementation of the XY-Cut method of layout
    analysis. https://en.wikipedia.org/wiki/Recursive_XY-cut
    """
    area = bitmap[lly:ury, llx:urx]
    x_vec, y_vec = area.sum(axis=0), area.sum(axis=1)

    lft, x_gaps, rgt = _gaps((x_vec/max(x_vec))<=thresh, llx, min_gap)
    btm, y_gaps, top = _gaps((y_vec/max(y_vec))<=thresh, lly, min_gap)

    # debugging
    if ax is not None:
        for x_gap in x_gaps:
            mid = sum(x_gap)/2
            ax.add_patch(
                Rectangle((mid-3, btm), 6, top-btm,
                          edgecolor='c', facecolor='c')
            )
    if ax is not None:
        for y_gap in y_gaps:
            mid = sum(y_gap)/2
            ax.add_patch(
                Rectangle((lft, mid-3), rgt-lft, 6,
                          edgecolor='c', facecolor='c')
            )
    
    cut_axis, mid = _best_cut_axis(
        x_gaps, y_gaps, (lft, btm, rgt, top), bitmap.shape, min_ratios
    )
    if cut_axis == 0:  # cut horizontally
        for zone in _find_zones(bitmap, llx, mid, urx, ury, min_gap,
                                min_ratios, thresh, ax=ax):
            yield zone
        for zone in _find_zones(bitmap, llx, lly, urx, mid, min_gap,
                                min_ratios, thresh, ax=ax):
            yield zone

    elif cut_axis == 1:  # cut vertically
        for zone in _find_zones(bitmap, llx, lly, mid, ury, min_gap,
                                min_ratios, thresh, ax=ax):
            yield zone
        for zone in _find_zones(bitmap, mid, lly, urx, ury, min_gap,
                                min_ratios, thresh, ax=ax):
            yield zone

    else:
        yield llx, lly, urx, ury

def _gaps(mask, offset, min_gap):
    gaps = []

    if len(mask) == 0:
        return 0, gaps, 0

    start, end = 0, len(mask)
    while start < end and mask[start]:
        start += 1
    while end > start and mask[end-1]:
        end -= 1

    pos = start
    for key, group in groupby(mask[start:end]):
        gaplen = len(list(group))
        if key and gaplen >= min_gap:
            gaps.append((pos, pos+gaplen))
        pos += gaplen

    return start+offset, gaps, end+offset

def _best_cut_axis(x_gaps, y_gaps, bbox, shape, min_ratios):
    cuts = []  # (size, axis, mid)
    lft, btm, rgt, top = bbox
    for x_gap in x_gaps:
        smaller = min(x_gap[0]-lft, rgt-x_gap[1])
        if (smaller/shape[1]) > min_ratios[0]:
            cuts.append((x_gap[1]-x_gap[0], 1, int(sum(x_gap)/2)))
    for y_gap in y_gaps:
        smaller = min(y_gap[0]-btm, top-y_gap[1])
        if (smaller/shape[0]) > min_ratios[1]:
            cuts.append((y_gap[1]-y_gap[0], 0, int(sum(y_gap)/2)))
    if cuts:
        return max(cuts)[1:]
    else:
        return (None, None)

def merge_lines(lines):
    # merge lines that overlap (e.g. super/subscripts)
    if not lines:  # no text content?
        return []


    merged_lines = [lines[0]]
    for line in lines[1:]:
        merged = False
        for line2 in merged_lines:
            if line.overlap(line2) >= min_line_overlap:
                line2.extend(line.tokens)
                merged = True
                break
        if not merged:
            merged_lines.append(line)
            # sort by page order and return
    return merged_lines
