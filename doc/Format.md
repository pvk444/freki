
# Description

The following is a sample of a Freki block that will be used to
perform language ID or IGT detection.

Each block has a preamble (or header) that precedes a list of lines.
Within this preamble are the following attributes:

* `doc_id` (refers to the original document that created the block)
* `page` (pdf page number of origin)
* `block_id` (unique block ID for this block)
* `bbox` (bounding box for the coordinates of the block)
  * The `bbox` format is `llx,lly,urx,ury`
  * `ll` stands for "lower left" and `ur` stands for "upper right"
  * The x coordinates are indexed from the left of the page, and
    the y coordinates from the bottom

Within each block, there are lines. These lines have the following
attributes:

* `tag=`:

  * There are three main tags:
    - `O`: this line is not IGT.
    - `B-`: this line is starting a new span of IGT
    - `I-`: this line is continuing a previous span of IGT

  * There are four types of `B` & `I` tags, too:
    - `M`: Metadata
    - `L`: language line
    - `G`: gloss line
    - `T`: translation line

  * There are attributes that we are not using for now, too, that are
    signified with `+`, these are things such as:
    - `DB`: double column
    - `AC`: Author Citation
    - `LN`: Language Name
    - ...and some others

* `lang=`: if the line contains IGT data, it should be labeled with
  the language's ISO-639-3 code

* `span_id=`: the unique id for the IGT span (starting from 1, and
  incrementing for each span)

* `fonts=`: The comma-delimited list of fonts used in this line of
  text in the format `<font_id>-<size.00>`


# Example

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
