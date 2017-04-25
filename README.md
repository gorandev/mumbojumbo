GovPredict Scraper

This project allows for several spiders. The GovPredict Scrapy item can be reused or subclassed for other spiders.

For the exercise I coded the FARA spider for Active Foreign Principals. It can be run by simple running `scrapy crawl fara` from the commandline, standing in the same folder where this README stands -- it will output the desired JSON to STDOUT.

There were two initial difficulties with this site:

1. The site requires some cookies to be present before actually relinquishing data.

So one couldn't just download an URL and get on with it. Luckily Scrapy has excellent cookie management and, by turning off the duplicate filter for the initial request, the cookies get set just like if it was a browser.

2. Pages were traversed using javascript.

The link for 'Next' needed to traverse the 30 pages or so of the report was a javascript link so we couldn't just harvest the URL. There's Splash, a library to run JS with Scrapy, but it was overkill for this. It was enough to use Firefox's console to take a look at the pagination and just replicate it with a Request object.

There was no User Agent set. Perhaps in a different scenario it would be worth to set a User Agent or even to randomize it.

Scrapy by default follows the robots.txt file and thus it wouldn't download anything from this site: that setting had to be turned off.

Also all requests were done from the same IP, one after the other. Other circumstances might require using open proxies, or maybe a couple VPNs. Scrapy Middleware makes it very easy.

For the data returned, the 'recent exhibit' field could be several PDFs but I chose to store only the URL for the most recent.

I had wrongly assumed that the 'state' field would be of no use for foreign principals, but the value is there on some pages, so I'm harvesting it.
