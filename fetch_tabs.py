import os, sys
import urllib2
from bs4 import BeautifulSoup
from urlparse import urljoin
import csv


#main_url = 'http://eusoils.jrc.ec.europa.eu/esdb_archive/EuDASM/Africa/indexes/idx_country.htm'
#main_url = 'http://eusoils.jrc.ec.europa.eu/esdb_archive/EuDASM/Asia/indexes/idx_country.htm'
main_url = 'http://eusoils.jrc.ec.europa.eu/esdb_archive/EuDASM/latinamerica/indexes/idx_country.htm'

map_field_name = 'MAP'

# match field table names >> Oracle Db field names
field_table = {'TITLE':'TITLE',
               'AUTHOR':'AUTHOR',
               'YEAR':'PUBLICATION_YEAR',
               'PUBLISHER':'PUBLISHER',
               'LANGUAGE':'LANGUAGE',
               'COORDINATES':None,
               'SCALE':'SCALE',
               'KEYWORDS':'KEYWORDS',
               map_field_name:'MAP',
               }

field_alias = {'PUBLISHER(S)':'PUBLISHER',
               'PUBLICATONYEAR':'YEAR',
               'PUBLICATIONYEAR':'YEAR',
               'AUTHOR(S)':'AUTHOR',
               'KEYWORD(S)':'KEYWORDS',
               }

# extra fields wil be attached as they are to all records, modify here for4 each CONTINENT!!!
extra_fields = {'CONTINENT':'South America',
                'IISN':'',
                'COUNTRY':'', # this will be replaced with the specific url (if available)
                'ISRICC':'',
                'REMARKS':'',
                'ZIP':'',
                'VISIBLE':1,
                'SCALETXT':'',
                'CONTID':5,   # 1:EUrope, 2:NorthAmerica, 3:ASia, 4:AFrica, 5:SouthAmerica, 6:OCeania, 7:ANtartica
                'CONT_ISO':'SA',
                }

complete_fields = [ "ISRICC","PUBLISHER","SCALETXT","SCALE","IISN",
                    "LANGUAGE","AUTHOR","COUNTRY","CONT_ISO","TITLE",
                    "MAP","CONTID","COORDINATES","CONTINENT","VISIBLE",
                    "REMARKS","YEAR","KEYWORDS","ZIP","ID" ]

divClass_listCountry = 'lastList'
divClass = 'lineMap'
imgClass = 'imgMap'
tabClass = 'tbMap'

str_to_remove = [ ":", " " ]

#starting ID, used as primary key for records dictionary
ID=30000
ID_field_name = 'ID'

### ==================================================================================

def delweird(obj):
    cleanobj = unicode(obj).encode('utf-8','replace')
    return ' '.join(str(cleanobj).split())

def remove_str(txt):
    newtxt = str(txt)
    for s in str_to_remove:
        newtxt = newtxt.replace(s,"")
        
    return newtxt

def checkforalias(field):

    if field in complete_fields:
        return field
    else:
        if field in field_alias.keys():
            return field_alias[field]
        else:
            print "...missing alias for: ", field
            sys.exit()

def get_tab_record(url,div):
    #get the tab inside the div
    tab = div.find('table',{'class':tabClass})

    #for each row of the table
    trs = tab.find_all('tr')
    record = {}
    for r in trs:
        #get field title and convert to upper case
        field = checkforalias( remove_str( r.find('th').getText() ).upper() )
        #get field value
        try:
            text = delweird( r.find('td').getText() )
        except AttributeError:
            text = ""
        #put inthe dic
        record[field] = text

    #get the image inside the div
    img = div.find('div', {'class':imgClass})
    try:
        record[map_field_name] = urljoin( url , img.find('a')['href'] )
    except:
        record[map_field_name] = ""
        print ".. source JPG Not Available: ",img.find('img')['src']
        
        
    #return a dic with existing fields from the table inside the div
    return record

def get_url_tabs(url,_fid):
    u = urllib2.urlopen(url)
    html = u.read()
    soup = BeautifulSoup(html)
    #get all nested tabs inside each main class div
    divs = soup.find_all('div', {'class':divClass})
    #for each div get the img and tab as a dic record
    records = {}
    for d in divs:
        records[_fid] = get_tab_record(url,d)
        _fid+=1

    del u,html,soup,divs

    return records

def attach_extra_fields(dic,extra_fields):
    newdic = dict(dic)

    for k in newdic.keys():
        newdic[k][ID_field_name] = k
        for f in extra_fields.keys():
            newdic[k][f] = extra_fields[f]
    return newdic

def get_sub_url(main_url):
    u = urllib2.urlopen(main_url)
    html = u.read()
    if os.path.exists(os.getcwd()+'/urls.txt'):
        f = open(os.getcwd()+'/urls.txt','r')
        html = ''.join(f.readlines())
        f.close()
        del f

    soup = BeautifulSoup(html)

    maindiv = soup.find('div',{'class':divClass_listCountry})
    #[(title,url),...]
    urls = [ ( u.getText() , urljoin( main_url , u['href']) )for u in maindiv.find_all('a') ]

    return urls

def save_to_csv(dic):

    #..save to csv (manual to keep utf8)
    with open('table_out.csv', 'wb') as csvfile:

        #use Oracle Db field names
        #fieldnames = [ f for f in dic[min(dic.keys())].keys() ]
        fieldnames = list(complete_fields)

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
                print dic[d]
                print "...Missing Fields:"
                print "add missing fields to possible fields alias"
                print sys.exc_info()[:]
                sys.exit()
            
### ==================================================================================

urls = get_sub_url(main_url)    

final_dic = {}
for url in urls:
    print "url: ",url[1]
    print "Country: ",url[0]
    r = get_url_tabs(url[1],ID)
    extra_fields['COUNTRY'] = url[0]
    r_plus = attach_extra_fields(r,extra_fields)
    print "..found ",len(r_plus.keys()),"records\n"
    for k in sorted(r_plus.keys()):
        final_dic[k] = r_plus[k]
    ID = max(r_plus.keys()) +1

print "Total records: ",len(final_dic.keys())
print "Total Countries: ", len(urls)

save_to_csv(final_dic)     
