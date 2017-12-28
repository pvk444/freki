# Freki

The following document explains the format of a Freki file. In addition, it notes a requirement for the installation of the Freki package.

## pdfminer.six

`pdfminer.six` is required in order to successfully run Freki using the `pdfminer` option.

### Installation

The following installation is recommended, as using the Python Package Index (PyPI) installs a broken version.

```
pip install https://github.com/goulu/pdfminer/zipball/e6ad15af79a26c31f4e384d8427b375c93b03533#egg=pdfminer.six
```

### Usage

To use `pdfminer.six`, run the following line in the Terminal: 

```
    pdf2txt.py -t xml input_pdf_file > output_xml_file
```

## Freki Format

The format of a Freki file is as follows:

A Freki file is divided into *blocks*. Blocks consist of a preamble (or 
header) as well as a following list of *lines*.

### Blocks

Each block begins with a preamble. The format of the preamble is the following:

```
doc_id=val1 block_id=val2 (attr3:val3) ... [<start_line>] [<end_line>]
```

(Note that `doc_id` and `block_id` should appear at the beginning of each block.)

Within the preamble are the following attributes:

(Note that the type of each attribute is listed as well: required, pre-defined but optional, and user-defined.)

* `doc_id`: Refers to the original document that was used to create the block [required]
* `page`: Page number of the original pdf document [pre-defined]
  * Must be an integer
* `block_id`: Unique ID for the block [required]
  * Format is `page-block_id`
    - e.g., `block_id=2-1` refers to the 1st block on page 2
* `bbox`: Bounding box for the coordinates of the block [pre-defined]
  * Format is `llx,lly,urx,ury`
    - `llx`, `lly`, `urx`, and `ury` are point coordinates
      - `ll` stands for "lower left"
      - `ur` stands for "upper right"
      - The x-coordinates (`llx` and `urx`) are indexed from the left of the page
      - The y-coordinates (`lly` and `ury`) are indexed from the bottom of the page
* `label`: Specifies the cuts that were made [pre-defined]
  * Format is [rltb]+
    - e.g., `rtll`
      - vertical; take the right one
      - horizontal; take the top one
      - vertical; take the left one
      - vertical; take the left one

The last two values, `start_line` and `end_line`, are optional. Although the following lines contain the start and end line information, they are redundantly listed for grepability.

### Lines

The format of a line is the following:

```
line=val1 (attr2:val2) ...
```

(Note that `line` should appear at the beginning of each block.)

Each line has the following attributes:

(Note that the type of each attribute is listed as well: required, pre-defined but optional, and user-defined.)

* `line`: Line number [required]
  * Must be an integer value
* `tag`: Specifies the content of the line [pre-defined]
  * There are three main tags:
    - `O`: This line is not IGT
    - `B-`: This line is starting a new span of IGT
    - `I-`: This line is continuing a previous span of IGT
  * There are also four types of `B` & `I` tags:
    - `M`: Metadata
    - `L`: Language line
    - `G`: Gloss line
    - `T`: Translation line
  * There are attributes that we are not using for now, too, that are
    signified with `+`; these are things such as:
    - `DB`: Double column
    - `AC`: Author citation
    - `LN`: Language name
* `lang`: ISO-639-3 code of the language (if the line contains IGT data)
* `span_id`: Unique ID for the IGT span
  * Starts at 1 and increments by 1 for each span
* `fonts`: List of fonts
  * Format is `font_id1-size1[,font2-size2]*`
  * e.g., `F0-12.0,F1-9.8`
    - Line has two fonts
    - First font: ID F0, size 12.0pt
    - Second font: ID F1, size 9.8pt 
* `bbox`: (see description of `bbox` for blocks) [pre-defined]
* `tabscore`: [pre-defined]
  * Real value between 0 and 1, inclusive

### Creating other attributes

Users can create other attributes, as needed.

For creating one's own attributes and values, there are a couple of requirements:
* Attribute names can be any string that does not contain whitespace, colons, or equal signs
* Values for other attributes can be any string that do not contain whitespace, colons, or equal signs

### Example

```
doc_id=3009.tetml page=11 block_id=11-6 bbox=42.5,660.3,500.4,672.3 365 365
line=365 tag=O fonts=F49-12.0:is a brick-town at speech time. As convincing as this may be, counterexamples are easy to find:


doc_id=3009.tetml page=11 block_id=11-7 bbox=42.5,615.7,506.2,641.6 366 367
line=366 tag=B-L lang=deu span_id=s13 fonts=F49-12.0:(xix) In der   Nachkriegszeit   ist Kleve   zu einer Klinkerstadt  geworden, aber  schon   in
line=367 tag=I-G lang=deu span_id=s13 fonts=F49-12.0:  	in the   after-war-time   is Kleve   to a	brick-town	become	but   already in


doc_id=3009.tetml page=11 block_id=11-8 bbox=70.8,574.2,453.4,600.1 368 369
line=368 tag=I-L lang=deu span_id=s13 fonts=F49-12.0:den  80ern   hat   man neue Impulse   gesetzt  in Richtung  Hochhaus
line=369 tag=I-G lang=deu span_id=s13 fonts=F49-12.0:the   80ies   has  one  new  impulses   set 	in direction   skyscrapers


doc_id=3009.tetml page=11 block_id=11-9 bbox=70.8,532.6,524.5,558.3 370 371
line=370 tag=I-T lang=deu span_id=s13 fonts=F49-12.0:'Kleve has become a brick-town after the War, but already in the 80ies, people tried new
line=371 tag=I-T lang=deu span_id=s13 fonts=F49-12.0:things with skyscrapers'


doc_id=3009.tetml page=11 block_id=11-10 bbox=56.6,501.9,503.7,513.9 372 372
line=372  tag=O fonts=F49-12.0:In the section about Comrie (1995) below, I will address other facets of the relevance-notion.
```
