# Freki

Freki is a package that takes the markup-language formatted output of 
a PDF-to-text extraction tool (Either [PDFLib TET][] or [PDFMiner][]),
and outputs text blocks that can be used for the subsequent
[IGT detection](https://github.com/xigt/igtdetect) and language ID
tasks.

## Sample Usage

#### TETML Input (Default)

	run_freki.py sample/sample.tetml.gz sample/sample_freki.txt
	
#### PDFMiner Input

    run_freki.py -f pdfminer sample.sample.pdfminer.txt sample/sample_pdfminer.txt

## Requirements

* Tested with python 2.7 and 3.5.

## Acknowledgements

Freki is part of the [Xigt Project][] and [ODIN][], and acknowledges
the same [sources of funding](http://depts.washington.edu/uwcl/odin/#acknowledgments).

[PDFLib TET]: https://www.pdflib.com/products/tet/
[PDFMiner]: https://github.com/euske/pdfminer
[Xigt Project]: https://github.com/xigt
[ODIN]: http://depts.washington.edu/uwcl/odin/
