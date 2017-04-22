# Freki

Freki is a package that takes the markup-language formatted output of 
a PDF-to-text extraction tool (Either [PDFLib TET][] or [PDFMiner][]),
and detects text *blocks* (e.g., paragraphs, headers, figures, etc.).
The blocks are assigned attributes (identifiers, bounding boxes, etc.)
for later analysis. This was developed for the detection of interlinear
glossed text (IGT), but it could serve other purposes, as well.

## Sample Usage

#### TETML Input (Default)

	run_freki.py sample/sample.tetml.gz sample/sample_freki.txt
	
#### PDFMiner Input

    run_freki.py -f pdfminer sample.sample.pdfminer.txt sample/sample_pdfminer.txt

## Requirements

* Python 3.3+
* [NumPy](http://www.numpy.org/)
* [Matplotlib](https://matplotlib.org/)

## Acknowledgements

Freki is part of the [Xigt Project][] and [ODIN][], and acknowledges
the same [sources of funding](http://depts.washington.edu/uwcl/odin/#acknowledgments).

[PDFLib TET]: https://www.pdflib.com/products/tet/
[PDFMiner]: https://github.com/euske/pdfminer
[Xigt Project]: https://github.com/xigt
[ODIN]: http://depts.washington.edu/uwcl/odin/
