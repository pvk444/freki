
import re
import logging

import numpy as np
# from scipy import ndimage
# for debugging
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from freki.analyzers import base
from freki.structures import Line, Block, Document


class XYCutAnalyzer(base.FrekiAnalyzer):
    def analyze(self, reader, id=None):
        doc = Document(id=id)

        bit_pages = [(p, _make_bitmap(p)) for p in reader.pages()]
        params = _parameters(bit_pages)

        for page, bitmap in bit_pages:
            logging.debug('Analyzing page id={}'.format(page.id))
            blocks = []
            tokens = page.tokens
            numtoks = len(tokens)

            if tokens:
                for i, zone in enumerate(_zones(bitmap, params, self._debug)):
                    bbox, path = zone
                    block = _zone_to_block(
                        tokens, bitmap, bbox, i+1, path, debug=self._debug
                    )
                    blocks.append(block)
        
            numtoks_b = sum(len(l.tokens) for b in blocks for l in b.lines)
            if numtoks_b != numtoks:
                logging.warning(
                    'Page {}: Different page-vs-block token counts: {} vs {}'
                    .format(page.id, numtoks, numtoks_b)
                )

            page.blocks = blocks
            doc.pages.append(page)

        return doc


def _make_bitmap(page):
    w, h = int(page.page_width), int(page.page_height)
    bitmap = np.zeros((h, w))
    for token in page.tokens:
        llx, lly = int(token.llx), int(token.lly)
        urx, ury = int(token.urx), int(token.ury)
        height = ury - lly
        dy = int(height/5)
        bitmap[lly      :lly+dy   , llx:urx] = token.height * 0.0
        bitmap[lly+dy   :lly+dy+dy, llx:urx] = token.height * 0.1
        bitmap[lly+dy+dy:ury-dy-dy, llx:urx] = token.height
        bitmap[ury-dy-dy:ury-dy   , llx:urx] = token.height * 0.1
        bitmap[ury-dy   :ury      , llx:urx] = token.height * 0.0

        # bitmap[lly:ury, llx:urx] = token.height
    return bitmap

# def _make_bitmap(page):
#     w, h = int(page.page_width), int(page.page_height)
#     bitmap = np.zeros((h, w))
#     for token in page.tokens:
#         llx, lly = int(token.llx), int(token.lly)
#         urx, ury = int(token.urx), int(token.ury)
#         height = ury - lly
#         rect = np.zeros((height + 2, urx - llx))
#         rect[1:height, :] = token.height
#         rect = ndimage.filters.gaussian_filter(rect, 1)
#         bitmap[lly:ury, llx:urx] = rect[1:-1,:]
#     return bitmap


def _zones(bitmap, params, debug=False):
    
    # try to clump nearby blocks through filters    
    # bitmap = ndimage.filters.maximum_filter(bitmap, size=(3,5))
    # bitmap = ndimage.filters.gaussian_filter(bitmap, 3, truncate=1)
    # bitmap /= bitmap.max()  # normalize

    # debugging
    ax=None
    if debug:
        fig, ax = plt.subplots()
        ax.imshow(bitmap, origin='lower')
        ax.autoscale(False)

    h, w = bitmap.shape
    bbox = (0, 0, w, h)
    for bbox, path in _find_zones(bitmap, bbox, '', params, ax=ax):
        
        llx, lly, urx, ury = bbox
        logging.debug(
            '  zone found: ({}, {}, {}, {})\t(width: {}, height: {}, path={})'
            .format(llx, lly, urx, ury, urx-llx, ury-lly, path)
        )
        if ax is not None:
            ax.add_patch(
                Rectangle((llx, lly), (urx-llx), (ury-lly),
                          edgecolor='w', facecolor='none')
            )

        yield bbox, path

    if debug:
        plt.show()


def _parameters(bit_pages):
    params = {
        # min sizes are minimum (height, width) ratios of resulting cuts
        'min_vcut_size': (1/32, 1/6),
        'min_hcut_size': (1/128, 1/6),
        'max_x_density': 0.0,
        'max_y_density': 0.0,
    }

    # use avg token height for both x and y minimum gap size
    tok_heights = []
    for page, bitmap in bit_pages:
        tok_heights.extend(t.height for t in page.tokens)
    h = (sum(tok_heights) / len(tok_heights)) if len(tok_heights) else 1
    params['min_x_gap'] = h
    params['min_y_gap'] = h

    # # infer minimum x and y gap by taking a histogram of page contents
    # # (this more sophisticated method unfortunately didn't work as well
    # #  as token height for the test documents)
    # xgaps, ygaps = [], []
    # for page, bitmap in bit_pages:
    #     xvec = bitmap.sum(axis=0)**3
    #     yvec = bitmap.sum(axis=1)**3
    #     xgaps.extend(_gaps(xvec, 0, 0.05, 0)[1])
    #     ygaps.extend(_gaps(yvec, 0, 0.05, 0)[1])
    # ds = np.array([b-a for a, b in xgaps])
    # params['min_x_gap'] = np.histogram(ds, bins='sqrt')[1][1]
    # ds = np.array([b-a for a, b in ygaps])
    # params['min_y_gap'] = np.histogram(ds, bins='sqrt')[1][1]

    logging.debug(
        ''.join('\n  {} = {}'.format(k, v) for k, v in params.items())
    )

    return params


def _find_zones(bitmap, bbox, path, params, ax=None):
    """
    This is a modified implementation of the XY-Cut method of layout
    analysis. https://en.wikipedia.org/wiki/Recursive_XY-cut
    """
    
    # possible optimization: check if area size is enough for any cut

    llx, lly, urx, ury = bbox
    area = bitmap[lly:ury, llx:urx]
    x_vec, y_vec = area.sum(axis=0), area.sum(axis=1)

    lft, x_gaps, rgt = _gaps(
        x_vec, params['min_x_gap'], params['max_x_density'], llx
    )
    btm, y_gaps, top = _gaps(
        y_vec, params['min_y_gap'], params['max_y_density'], lly
    )

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
        x_gaps, y_gaps, (lft, btm, rgt, top), bitmap.shape,
        params['min_vcut_size'], params['min_hcut_size']
    )
    if cut_axis == 0:  # cut horizontally
        inner_bbox = (llx, mid, urx, ury)
        for zone in _find_zones(bitmap, inner_bbox, path+'t', params, ax=ax):
            yield zone
        inner_bbox = (llx, lly, urx, mid)
        for zone in _find_zones(bitmap, inner_bbox, path+'b', params, ax=ax):
            yield zone

    elif cut_axis == 1:  # cut vertically
        inner_bbox = (llx, lly, mid, ury)
        for zone in _find_zones(bitmap, inner_bbox, path+'l', params, ax=ax):
            yield zone
        inner_bbox = (mid, lly, urx, ury)
        for zone in _find_zones(bitmap, inner_bbox, path+'r', params, ax=ax):
            yield zone

    else:
        yield bbox, path


def _gaps(vec, min_gap, max_density, offset):
    gaps = []

    start, end = offset, len(vec) + offset
    if end > start:
        vec = np.pad(vec/(vec.max() or 1), ((1,1)),
                     'constant', constant_values=1)
        gaps = np.reshape(np.where(np.diff(vec <= max_density)), (-1,2))
        gaps += offset
    if len(gaps) and gaps[0][0] == start:
        start, gaps = gaps[0][1], gaps[1:]
    if len(gaps) and gaps[-1][1] == end:
        end, gaps = gaps[-1][0], gaps[:-1]
    if len(gaps):
        gaps = [(a, b) for a, b in gaps if b-a >= min_gap]
    return start, gaps, end


def _best_cut_axis(x_gaps, y_gaps, bbox, shape, min_vcut_size, min_hcut_size):
    cuts = []  # (size, axis, mid)
    lft, btm, rgt, top = bbox
    for x_gap in x_gaps:
        h_ratio = (top - btm) / shape[0]
        w_ratio = min(x_gap[0]-lft, rgt-x_gap[1]) / shape[1]
        if h_ratio >= min_vcut_size[0] and w_ratio >= min_vcut_size[1]:
            cuts.append((x_gap[1]-x_gap[0], 1, int(sum(x_gap)/2)))
    for y_gap in y_gaps:
        h_ratio = min(y_gap[0]-btm, top-y_gap[1]) / shape[0]
        w_ratio = (rgt - lft) / shape[1]
        if h_ratio >= min_hcut_size[0] and w_ratio >= min_hcut_size[1]:
            cuts.append((y_gap[1]-y_gap[0], 0, int(sum(y_gap)/2)))
    if cuts:
        return max(cuts)[1:]
    else:
        return (None, None)

def _zone_to_block(tokens, bitmap, bbox, id, path, debug):
    llx, lly, urx, ury = bbox
    tokens = list(filter(_bbox_filter(llx, lly, urx, ury), tokens))
    block = Block(id=id, label=path)

    btm, y_gaps, top = _gaps(bitmap[lly:ury, llx:urx].max(axis=1), 0, 0, lly)
    mids = [sum(gap)/2 for gap in y_gaps]
    for btm, top in zip([lly] + mids, mids + [ury]):
        ts = list(filter(_bbox_filter(llx, btm, urx, top), tokens))
        if ts:
            line = Line(ts)
            line.sort()
            block.append(line)

    block.sort()
    return block


def _bbox_filter(llx, lly, urx, ury):
    def bbox_filter(t):
        # +- 1 for rounding problems in the bitmap. This
        # should not capture extra characters unless they already
        # overlapped (1pt height characters are probably rare)
        return (
            t.llx >= llx - 1 and
            t.lly >= lly - 1 and
            t.urx <= urx + 1 and
            t.ury <= ury + 1
        )
    return bbox_filter
