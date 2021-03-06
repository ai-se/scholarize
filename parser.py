from __future__ import print_function, division
__author__ = 'george'
import requests, sys
from lxml import html, etree
import time, traceback


ALL_CONFS = "https://scholar.google.com/citations?view_op=top_venues&hl=en&vq=eng_softwaresystems"
BASE_URL = "https://scholar.google.com"

class O():
  def __init__(self, **d): self.has().update(**d)
  def has(self): return self.__dict__
  def update(self, **d) : self.has().update(d); return self
  def __repr__(self)   :
    show=[':%s %s' % (k,self.has()[k])
      for k in sorted(self.has().keys() )
      if k[0] is not "_"]
    txt = ' '.join(show)
    if len(txt) > 60:
      show=map(lambda x: '\t'+x+'\n',show)
    return '{'+' '.join(show)+'}'
  def __getitem__(self, item):
    return self.has().get(item)

class Conference(O):
  def __init__(self, name, url):
    O.__init__(self, name=name, url=url)

  def fetch_papers(self, start=0):
    conf_url = self.url + "&cstart=" + str(start)
    tree = fetch(conf_url)
    table = tree.xpath("//table[@id='gs_cit_list_table']")[0]
    rows =  table.findall("tr")
    papers = []
    for row in rows[1:]:
      # Skipping tile rows
      cols = row.findall("td")
      url = cols[0].find("a").get("href")
      name = cols[0].find("a").find("span").text
      spans = cols[0].findall("span")
      authors = spans[0].text
      publication = spans[1].text
      citations = cols[1].find("a").text
      year = cols[2].text
      papers.append(Paper(conference = self.name, year = year,
                          name = name, authors = authors,
                          citations = citations, publication = publication, url = url))
    if len(rows) == 21:
      # Skipping tile rows
      papers += self.fetch_papers(start + len(papers))
    return papers



class Paper(O):
  def __init__(self, **params):
    O.__init__(self, **params)

  def to_csv(self):
    sep = "\t"
    ret_str = self.conference + sep + \
           self.year + sep + \
           self.name + sep + \
           self.authors + sep + \
           self.citations + sep + \
           self.publication + sep + \
           self.url
    ret_str = ret_str.encode('ascii', 'ignore')
    return ret_str


def fetch(url):
  headers = {'User-Agent': 'Mozilla/5.0 (X11; U; FreeBSD i386; en-US; rv:1.9.2.9) Gecko/20100913 Firefox/3.6.9'}
  page = requests.get(url, headers)
  print(url, page.status_code)
  time.sleep(10)
  tree = html.fromstring(page.content)
  return tree

def parse_conferences(tree):
  table = tree.xpath("//table[@id='gs_cit_list_table']")[0]
  rows =  table.findall("tr")
  conferences = []
  for row in rows[1:]:
    # Skipping tile rows
    cols = row.findall("td")
    name = cols[1].text
    url = BASE_URL + cols[2].find("a").get("href")
    conferences.append(Conference(name, url))
  return conferences

def run():
  tree = fetch(ALL_CONFS)
  conferences = parse_conferences(tree)
  papers = []
  failed = {}
  for conference in conferences:
    try:
      papers += conference.fetch_papers()
    except Exception:
      failed[conference.name] = conference.url
      print(traceback.format_exc())
  f = open("scholar.tsv", "w")
  f.write("Conference\tYear\tName\tAuthors\tCitations\tPublication\tURL\n")
  for paper in papers:
    f.write(paper.to_csv() + "\n")
  f.close()
  f = open("failed.tsv", "w")
  for key, val in failed.items():
    f.write(key + "\t" +  val + "\n")
  f.close()

def run_failed():
  conferences = []
  with open('failed.tsv') as f:
    for line in f:
      params = line.replace("\n","").split("\t")
      conferences.append(Conference(params[0], params[1]))
  papers = []
  failed = {}
  for conference in conferences:
    try:
      papers += conference.fetch_papers()
    except Exception:
      failed[conference.name] = conference.url
      print(traceback.format_exc())
  f = open("scholar.tsv", "a")
  for paper in papers:
    f.write(paper.to_csv() + "\n")
  f.close()
  f = open("failed.tsv", "w")
  for key, val in failed.items():
    f.write(key + "\t" +  val + "\n")
  f.close()


if __name__ == "__main__":
  args = sys.argv
  if args[1] == "all":
    run()
  elif args[1] == "failed":
    run_failed()