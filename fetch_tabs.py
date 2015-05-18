import os, sys
import urllib2
from bs4 import BeautifulSoup
from urlparse import urljoin
import csv


main_url = 'http://eusoils.jrc.ec.europa.eu/ESDB_Archive/eusoils_docs/doc.html'
base_url = 'http://eusoils.jrc.ec.europa.eu/ESDB_Archive/eusoils_docs/'

def delweird(obj):
    cleanobj = unicode(obj).encode('utf-8','replace')
    return ' '.join(str(cleanobj).split())

def emptylbl(lbl):
    if len(lbl)==0:
        return "download"
    else:
        return lbl

    
def get_url_tabs(url,maindivid):
    u = urllib2.urlopen(url)
    html = u.read()
    soup = BeautifulSoup(html)
    #get all nested tabs inside each main class div
    tabs = soup.find_all('table')
    #div = soup.find('div',{'id':maindivid})
    #rows = div.find_all('tr')

    return tabs#rows

def get_td(row):
    pass
    return row.find_all('td')

def save_to_csv(dic):

    #..save to csv (manual to keep utf8)
    with open('table_out.csv', 'wb') as csvfile:

        #use Oracle Db field names
        #fieldnames = [ f for f in dic[min(dic.keys())].keys() ]
        fieldnames = ['ID','Group','No','Title','Image','Download_lbl','Download_lnk']

        spamwriter = csv.DictWriter(csvfile, fieldnames=fieldnames,
                                    delimiter='|',
                                    quotechar='"', quoting=csv.QUOTE_NONNUMERIC,
                                    lineterminator='\n', restval='', dialect='excel')
        spamwriter.writeheader()

        for d in sorted(dic.keys()):
            #print d
            try:
                spamwriter.writerow( dic[d] )
            except ValueError:
                print fieldnames
                #print dic[d]
                print "...Missing Fields:"
                print "add missing fields to possible fields alias"
                print sys.exc_info()[:]
                sys.exit()

            
### ==================================================================================

final_dic = {}
main_url
print "url: ",main_url
maindivid = "content"
tabs = get_url_tabs(main_url,maindivid)

ID = 0
for t in tabs:
    rows = t.find_all('tr')
    first_row = rows[0].find_all('td')
    print '|'.join([delweird(r.getText()) for r in first_row])
    gettab = raw_input('\nGet table? (y/n): ')
    print '\n\n'

    if gettab == 'y':
        tab_title = raw_input('Table Title: ')
        for r in range(1,len(rows)):
            dic = {}
            row = rows[r].find_all('td')
            dic['ID'] = ID
            dic['Group'] = tab_title
            dic['No'] = row[0].getText()
            dic['Title'] = delweird(row[1].getText())
            try:
                dic['Image'] = urljoin( base_url , row[2].find('img')['src'] )
            except:
                dic['Image'] = ''
            try:
                hrefs = row[1].find_all('a')
                lbls = []
                links = []
                for h in hrefs:
                    try:
                        links.append( urljoin(base_url ,h['href']) )
                        lbls.append( emptylbl(delweird(h.getText())) )
                    except KeyError:
                        pass # <a> without href
                dic['Download_lbl'] = ';'.join(lbls)
                dic['Download_lnk'] = ';'.join(links)

            except:
                print row[1].find_all('a')
                print sys.exc_info()
                raw_input('Error stop.')
                sys.exit()
            final_dic[ID] = dic
            ID+=1

##for k in sorted(r.keys()):
##    final_dic[k] = r[k]
##
print "Total records: ",len(final_dic.keys())
##
save_to_csv(final_dic)     
