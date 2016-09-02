# About
Freki is a package that takes the markup-language formatted output of 
a pdf-to-text extraction tool (Either PDFLib TET or PDFMiner), and
outputs text blocks that can be used for the subsequent IGT detection
and language ID task tools.
## Sample Usage

#### TETML Input (Default)
	freki.py sample/sample.tetml.gz sample/sample_freki.txt
	
#### PDFMiner Input
    freki.py -f pdfminer sample.sample.pdfminer.txt sample/sample_pdfminer.txt
