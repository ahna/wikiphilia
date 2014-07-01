# Wikiscore

This simple web app lives at http://www.wikiscore.co

Wikipedia is a living encyclopedia. Because it is crowdsourced, it differs from a 
traditional encyclopedia in that there is no single editor, resulting in uneven editorial
quality. Some pages have a single contributor, perhaps a student across the world. Other
pages have thousands of editors vetting and debating the content in real time. Further,
internet software now draws information directly from Wikipedia, such as the Google
sidebar. As such, Wikipedia often provides the first exposure to new information.

To address the unevenness in quality, I developed the Wikiscore: a quality measure for Wikipedia
pages. The Wikiscore algorithm is a work in progress, and I'd be happy for others to help refine it. 
It currently measures five features on each page:
1. Flesch-Kincaid Readibility Grade Level 
2. Number of links to other Wikipedia pages
3. Number of links to external websites
4. Length of the introduction
5. Number of images

I scraped 100k Wikipedia pages and put their features in a database. In order for my 
algorithm to learn what a quality page looked like, I used featured Wikipedia pages as a 
proxy for "high quality" (4248 pages) and flagged Wikipedia pages as a proxy for "low 
quality" (2468 pages). I used a random forest classifier with a 60/40 train/test split 
and achieved ~96% accuracy, precision and recall on the test set. Thus the challenge 
isn't about distinguishing featured and flagged pages. The challenge is in refining the 
algorithm to make meaningful Wikiscores. I drastically improved the meaningfulness of 
the Wikiscore by removing all features related to page length (such as number of words). 

This program uses:
Python, the Natural Language Toolkit, the MediaWiki API, MySQL, Sci-kit Learn, Beautiful Soup
