#!/usr/bin/python

import os, sys

# Pages begin as follows:

#     <hr>
#     <A name=2></a>1<br>

# Beginning at page 4, the second number is an increasing page number:

#     <hr>
#     <A name=4></a>1<br>
# ...
#     <hr>
#     <A name=5></a>2<br>

# This is the number printed in the top-right hand corner
# of the original PDF.

HR = "<hr>\n"
BEGIN = "***OOO***<br>\n"

# Lines are numbered:

# 14<br>
# THE COURT:<br>
# GOOD MORNING.<br>
# 15<br>
# ALL RESPOND:<br>
# GOOD MORNING.<br>

BR = "<br>\n"

PRINT_PRE = False

def parsePreamble(o, i):
    p = 0
    print "preamble", p
    lastLineNo = None
    pageAnchor = None

    for line in i:
        if line == BEGIN:
            print >>o, '<p class="narration">***OOO***</p>'
            return p, lastLineNo, pageAnchor

        if line == HR:
            p += 1
            print "preamble", p
            if PRINT_PRE:
                print >>o, line
            continue
        if line.startswith('<A '):
            pageAnchor = line
            if PRINT_PRE:
                print >>o, line
            continue

        if not line.endswith(BR):
            print "SKIP", line,
            continue
        line = line[0:-len(BR)]
        
        if line[0].isdigit():
            try:
                lastLineNo = int(line)
            except ValueError:
                if PRINT_PRE:
                    print >>o, line, BR,
        else:
            if PRINT_PRE:
                print >>o, line, BR,
    
    assert False


corrections = [
    (' star war ', ' Star Wars '),
    (' yzaca ', ' ycaza '),
    ]

icons = {
    'Mr. Richardson': 'richardson.jpg',
    'The Respondent': 'leif.png',
    'The Witness': 'banks.jpg',
    'A': 'banks.jpg',
    'by mr. richardson:': 'richardson.jpg',
    'by the court:': 'avatar.png',
    'by the respondent:': 'leif.png',
}

examiner = None

class Dialogue:
    def __init__(self, pageNo, lastLineNo, speaker):
        self.pageNo = pageNo
        self.lineNo = lastLineNo
        speaker = speaker.lower().title()
        self.speaker = speaker
        self.lines = []
        self.words = []
        if speaker == 'Q':
            self.icon = icons[examiner]
        else:
            self.icon = icons.get(speaker, 'avatar.png')
    
    def addLine(self, line):
        l = line.lower()
        if l.startswith('by '):
            global examiner
            examiner = l
        elif l == 'constantine evans,':
            icons['The Witness'] = 'costi.png'
            icons['A'] = 'costi.png'
        for r in corrections:
            l = l.replace(r[0], r[1])
        self.lines.append(l)
        self.words.extend(l.split())


def switchDialogue(o, dialogue, pageNo, lastLineNo, speaker):
    if dialogue:
        printDialogue(o, dialogue)
    dialogue = Dialogue(pageNo, lastLineNo, speaker)
    return dialogue


def parsePageAnchor(anchor):
    # e.g.,
    #   <A name=38></a>35<br>
    # The first number is produced by the pdftohtml conversion;
    # the second is the one printed in the top-right of
    # the original PDF.
    return int(anchor.split('>')[2].split('<')[0])
    

def parsePage(o, i, p, pageAnchor, dialogue, lastLineNo = None):
    global examiner
    print "page", p
    
    prevLineNo = None
    pageNo = parsePageAnchor(pageAnchor)
    print >>o, '<a name=p%02d></a>' % (pageNo, )

    for line in i:
        # these are eaten by the outer loop
        assert not line.startswith('<A ')
        
        if line == HR:
            break # end of page

# 16<br>
# THE COURT:<br>
# AS YOU CAN SEE, WE HAVE A BUSY<br>
# 17<br>
# CALENDAR THIS MORNING.<br>
# I HAVE A PRIORITY FOR MATTER<br>
# 18<br>
# NUMBER 13, WHICH IS CASTLE VERSUS STRAND.<br>

        if not line.endswith(BR):
            # HTML tags at begin/end
            print "SKIP", line,
            assert line[0] == '<'
            continue
        
        line = line[0:-len(BR)]
        
        if line[0].isdigit():
            try:
                lastLineNo = int(line)
                if prevLineNo and lastLineNo == prevLineNo+1:
                    if dialogue and dialogue.speaker == 'Narrator':
                        printDialogue(o, dialogue)
                        dialogue = None
                    else:
                        dialogue = switchDialogue(o, dialogue, pageNo, lastLineNo, speaker='Narrator')
                prevLineNo = lastLineNo
            except ValueError:
                dialogue.addLine(line)
                prevLineNo = None
        
        elif line.endswith(':'):
            if line.count(' ') < 2:
                if dialogue is None or dialogue.speaker != 'Narrator':
                    dialogue = switchDialogue(o, dialogue, pageNo, lastLineNo, speaker=line[0:-1])
                else:
                    if line != 'THE COURT:':
                        dialogue.addLine(line)
                    dialogue = switchDialogue(o, dialogue, pageNo, lastLineNo, speaker=line[0:-1])
                    prevLineNo = None
            else:
                if dialogue.speaker == 'Narrator':
                    dialogue.addLine(line)
                    printDialogue(o, dialogue)
                    dialogue = None
                else:
                    dialogue.addLine(line)
                prevLineNo = None
        elif line in ('Q','A'):
            dialogue = switchDialogue(o, dialogue, pageNo, lastLineNo, speaker=line)
        elif line.startswith('(WHEREUPON,'):
            dialogue = switchDialogue(o, dialogue, pageNo, lastLineNo, speaker='Narrator')
            dialogue.addLine(line)
            prevLineNo = None
        else:
            if not dialogue or (line == '///' and dialogue.speaker != 'Narrator'):
                dialogue = switchDialogue(o, dialogue, pageNo, lastLineNo, speaker='Narrator')
            dialogue.addLine(line)
            prevLineNo = None

    return dialogue


# from Pygments:
# <span class="lineno"> 6 </span><span class="p">{</span>
LINENO = '<span class="lineno">%2d </span>'
printLineNumbers = False # XXX: anchor

def printDialogue(o, dialogue):
    if printLineNumbers:
        print >>o, (LINENO % dialogue.lineNo),
    print >>o, '<a name=p%02dl%02d></a>' % (dialogue.pageNo, dialogue.lineNo)
    if dialogue.speaker == 'Narrator':
        print >>o, '<p class="narration">'
    else:
        if dialogue.icon:
            print >>o, ('<p class="spk"><img src="%s" width=48 height=48 align=bottom> %s</p><p class="dlg">' % (dialogue.icon, dialogue.speaker))
        else:
            print >>o, ('<p class="spk">%s</p><p class="dlg">' % dialogue.speaker)
    if False:
        for line in dialogue.lines:
            print >>o, line,
    else:
        printWords(o, dialogue.words)
    print >>o, '</p>'
    return


properNames = set([
    'god',
    'castle', 'green', 'homeowners', 'association', "association's",
    'leif', 'strand',
    'dianne', 'patrizzi', "dianne's",
    'randy', 'banks',
    'kelly', 'richardson',
    'constantine', 'evans',
    'richard', 'ycaza',
    'cathy', 'brown',
    'i', "i'm", "i'll", "i've",
    'mr.',
    'association',
    'treasurer', 'president', 'chairman',
    'pasadena',
    'south', 'el', 'molino', 'avenue',
    'twitter',
    'slack',
    'wednesday', 'september', 'october',
    ])

from collections import deque
renter = deque()
renter.append('/baby/vm-2016-07-21.mov')
renter.append('/baby/vm-2016-07-22-1.mov')
renter.append('/baby/vm-2016-07-22-2.mov')
renter.append('/baby/vm-2016-08-04.mov')

links = {
    '&quot;slack.&quot;': '''&quot;<a href="https://slack.com/">Slack</a>.&quot;''',
    'newsletters': '<a href="/havisham/v2i1.pdf">newsletters</a>',
}

def printWords(o, words):
    # "I was afraid of worms, Roxanne!"
    
    newSentence = True
    lastWord = None
    for word in words:
        if newSentence:
            word = word.capitalize()
            newSentence = False

        if word in properNames or (word[-1] in '.,?!' and word[:-1] in properNames):
            word = word.capitalize()
        if 'pdro' in word:
            # case number
            word = word.upper()
        if max(word.count('-'), word.count('.')) > 1:
            # e.g., H.O.A. or B-A-N-K-S
            # BUG: capitalizes 'MAN-TO-MAN', which is funny, so I left it in
            word = word.upper()

        if word[:6] == 'renter':
            url = renter.popleft()
            word = '<a href="%s">renter</a>%s' % (url, word[6:])
        elif word in links:
            word = links[word]
        elif word == '///' and lastWord != '///':
            print >>o, '<br>'
        
        print >>o, word,
        lastWord = word
        
        if word == '///':
            print >>o, '<br>'
        
        if word[-1] in '.?!':
            newSentence = True

    return


def main():
    i = open("input.html", "r")
    o = open("index.html", "w");
    print >>o, HEAD
    print >>o, '<div class="transcript"><tt>'
    p, lastLineNo, pageAnchor = parsePreamble(o, i)
    dialogue = parsePage(o, i, p, pageAnchor, None, lastLineNo)
    for line in i:
        if line == '</BODY>\n':
            break
        assert line.startswith('<A '), line
        pageAnchor = line
        dialogue = parsePage(o, i, p, pageAnchor, dialogue)
        p += 1
    printDialogue(o, dialogue)
    print >>o, '</tt></div>'
    print >>o, TAIL
    o.close()
    i.close()
    return



HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8">
<title>Dark Castle &mdash; The Court Hearing</title>

	<link rel="stylesheet" media="screen" href="/style/219.css">
	<link rel="stylesheet" media="screen" href="/style/transcript.css">
	<link rel="alternate" type="application/rss+xml" title="RSS" href="http://www.csszengarden.com/zengarden.xml">

	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta name="author" content="Leif Strand">
	<meta name="description" content="A part of The Nemesis Project">
	<meta name="robots" content="all">

	<script src="http://use.typekit.net/fzq7emy.js"></script>
	<script>try{Typekit.load();}catch(e){}</script>

	<!--[if lt IE 9]>
	<script src="/scripts/html5shiv.js"></script>
	<![endif]-->
</head>
<body>
<div class="page-wrapper">

	<section class="intro">
		<header role="banner">
			<h1>Dark Castle</h1>
			<h2>The Restraining Order</h2>
		</header>
	</section>

	<div class="main supporting" role="main">
		<div class="explanation" role="article">
			<h3>The Court Hearing</h3>
			<p>Thursday, October 18, 2018</p>
"""

TAIL = """
		</div>
	</div>
	<div class="main supporting" role="main">
		<div class="explanation" role="article">
<p><a href="PDF_T18T54_CASTLE_GREEN_VS_STRAND_10-18-18_FINAL_TRANSCRIPT.pdf">Original PDF document</a> translated to <a href="PDF_T18T54_CASTLE_GREEN_VS_STRAND_10-18-18_FINAL_TRANSCRIPT.html">HTML</a> using <a href="http://pdftohtml.sourceforge.net/"><tt>pdftohtml</tt></a> version 0.40.</p>
<p>Dark Castle presentation produced by <a href="https://github.com/castlegreen/hulk/blob/master/transcribe.py"><tt>transcribe.py</tt></a>.</p>
		</div>
    </div>
	<div class="main supporting" role="main">
		<div class="explanation" role="article">
<p class="runic"><img src="/images/nice-girl.jpg" width=212 height=154></p>
<p class="runic">&#x2F2D; &#x2F76; &#x2F65;</p>
		</div>
	</div>

</div>
</body>
</html>
"""


main()

