#!/usr/bin/env python3.6
import time,mwclient
def getTransclusions(site,page,sleep_duration = None,extra=""):
    cont = None;
    pages = []
    i = 1
    while(1):
        result = site.api('query',list='embeddedin',eititle=str(page),eicontinue=cont,eilimit=500,format='json')
        print("got here")
        if sleep_duration is (not None):
            time.sleep(sleep_duration)
        #res2 = result['query']['embeddedin']
        for res in result['query']['embeddedin']:
            print('append')
            pages.append(str(i) + " " + res['title'])
            i +=1
        try:
            cont = result['continue']['eicontinue']
            print("cont")
        except NameError:
            print("Namerror")
            return [pages,i]
        except Exception as e:
            print("Other exception" + str(e))
        #    print(pages)
            return [pages,i]
site = mwclient.Site(('https','en.wikipedia.org'), '/w/')
f = open('./res.txt','a+')
result = getTransclusions(site,"Template:GA nominee")
print(result[1])
for n in result[0]:
    #print(n + "\n")
    f.write(n + "\n")
f.close()
#getTransclusions(site,"Template:GA Nominee") + "\n"
