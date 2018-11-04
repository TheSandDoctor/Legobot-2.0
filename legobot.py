#!/usr/bin/env python3.6
import mwparserfromhell
import toolforge
import mwclient  # TODO: clean up mwclient imports
import pymysql
import credentials
from mwclient import *
from datetime import *
from dateutil import *
import time
import re 
import sys

# Source I am converting from:
# https://github.com/legoktm/harej-bots/blob/master/goodarticles.php
botuser = 'Legobot'
databasename = 's53824__legobot2'


def allow_bots(text, user):
    user = user.lower().strip()
    text = mwparserfromhell.parse(text)
    for tl in text.filter_templates():
        if tl.name in ('bots', 'nobots'):
            break
    else:
        return True
    for param in tl.params:
        bots = [x.lower().strip() for x in param.value.split(",")]
        if param.name == 'allow':
            if ''.join(bots) == 'none': 
                return False
            for bot in bots:
                if bot in (user, 'all'):
                    return True
        elif param.name == 'deny':
            if ''.join(bots) == 'none': 
                return True
            for bot in bots:
                if bot in (user, 'all'):
                    return False
    return True


def getUserID(username):
    result = site.api('query', list='users', ususers=username, format='json')
    return result['query']['users'][0]['userid']


def add_icon(title):
    mainPage = site.Pages[title]
    text = mainPage.text()
    if (re.search(r'\{\{good( |_)article\}\}', text, re.I) is None and allow_bots(text, botuser)):
        savetext = "{{good article}}\n{}".format(text)
        mainPage.save(savetext, summary="Adding Good Article Icon", bot=True, minor=True)


def getTransclusions(site, page, sleep_duration=None, extra=""):
    cont = None
    pages = []

    while True:
        result = site.api('query', list='embeddedin', eititle=str(page), eicontinue=cont, eilimit=500, format='json')
        print("got here")
        if sleep_duration is (not None):
            time.sleep(sleep_duration)
        # res2 = result['query']['embeddedin']
        for res in result['query']['embeddedin']:
            print('append')
            pages.append(res['title'])
        try:
            cont = result['continue']['eicontinue']
            print("cont")
        except NameError:
            print("Namerror")
            return pages
        except Exception as e:
            print("Other exception" + str(e))
            #    print(pages)
            return pages

class GANom:
    def __init__(self, article, template = None):
        self.unixtime = time.time()
        self.timestamp = "Error parsing timestamp."
        self.reviewpage = False
        self.reviewer = 'Example'
        self.reviewerRaw = '[[User:Example|Unknown]]'
        self.subtopic = 'Miscellaneous'
        self.status = 'new'
        self.valid_statuses = ['new', 'passed', 'failed', 'on hold', 'on review', '2nd opinion']
        self.nominator = '[[User:Example|Unknown]]'
        self.nominator_plain = 'Example'
        self.note = False
        self.article = article.strip()
        
        if template is not None:
            self.parse_template(template)

    def parse_template(self, template):
        if template.has("1"):  # timestamp
            self.timestamp = template.get("1").value.strip()
            self.set_time(template.get("1").value)
            
        if template.has("nominator"):  # nominator
            self.set_nominator(template.get("nominator").value)
            
        if template.has("page"):  # page
            self.set_review_page(template.get("page").value)
            
        if template.has("status"):  # status
            if template.get("status").value:
                self.set_status(template.get("status").value)

        if template.has("subtopic"):  # subtopic
            self.set_subtopic(template.get("subtopic").value)

        if template.has("note"):  # note
            self.set_note(template.get("note").value)

    def set_time(self, timestamp):
        unix = time.mktime(parser.parse(str(timestamp[:-6])).timetuple())
        if unix is False:
            return False
        self.unixtime = unix

    def set_review_page(self, page):
        page = page.split()
        if re.search(r'^[0-9]+$', page[0]):
            self.reviewpage = page

    def set_subtopic(self, topic):
        try:
            topic = topic.replace(", and", " and").strip()
        except ValueError:
            pass
        
        if topic:
            self.subtopic = topic

    def set_status(self, status):
        status = str(status)
        cleanedStatus = self.cleanStatus(status)
        if cleanedStatus in self.valid_statuses:
            self.status = cleanedStatus

    def cleanStatus(self, status):
        if re.search(r'(on ?)?hold', status, re.IGNORECASE):
            return 'on hold'
        elif re.search(r'(on ?)?review', status, re.IGNORECASE):
            return 'on review'
        elif re.search(r'(2nd|second|2)? ?op(inion)?', status, re.IGNORECASE):
            return '2nd opinion'
        return status

    def set_nominator(self, nominator):
        if nominator:
            nominator = nominator.strip()
            self.nominator = nominator
            m = re.search(r"\[\[User:(.+?)\|.+?\]\]", nominator)
            if m.group(1):
                nom = m.group(1).replace('_', ' ')
                nom = nom[0].upper() + nom[1:]
                self.nominator_plain = nom.strip()

    def set_note(self, note):
        note = note.strip()
        if note:
            self.note = note

    def set_reviewer(self, reviewer, raw=False):
        reviewer = reviewer.strip()
        if reviewer:
            self.reviewer = reviewer
            self.reviewerRaw = "{{user|" + reviewer + "}}"
        if raw:
            self.reviewerRaw = raw

    def numOfReviews(self, name):
        global gaStats
        nameFound = next((item for item in gaStats if item["name"] == name), False)
        if nameFound:
            return "(Reviews: {}) ".format(nameFound["reviews"])

    def existsThingyGahhh(self):
        if self.status is 'new':
            return ''
        else:
            return '|exists=yes'

    def miniWikiCode(self):
        return "# {{GANentry|1=" + self.article + "|2=" + self.reviewpage + "}}"

    def wikicode(self):
        code = "# {{GANentry|1=" + self.article + "|2=" + self.reviewpage + self.existsThingyGahhh() + "}} " + self.numOfReviews(
            self.nominator_plain) + self.nominator + " " + self.timestamp + "\n"
        if self.status is "on hold":
            code += "#:{{GAReview|status=on hold}} " + self.numOfReviews(self.reviewer) + self.reviewerRaw + "\n"
        elif self.status is "2nd opinion":
            code += "#:{{GAReview|status=2nd opinion}} " + self.numOfReviews(self.reviewer) + self.reviewerRaw + "\n"
        elif self.status is "on review":
            "#:{{GAReview}} " + self.numOfReviews(self.reviewer) + self.reviewerRaw + "\n"
        if self.note:
            code += "#: [[File:Ambox_notice.png|15px]] '''Note:''' " + self.note + "\n"
        return code

        
print("Logging in...")
site = mwclient.Site(('https', 'en.wikipedia.org'), '/w/')
try:
    site.login(credentials.username, credentials.password)
except:
    print("Error with logging in")
    sys.exit(0)

print("Retrieving database login credentials...")
# Might like to use ConfigParser
with open('/data/project/legobot-2/replica.my.cnf', 'r') as iniFile:
    splitIni = iniFile.splitlines()
    forgeUsername = splitIni[1]
    forgePassword = splitIni[2]
    print("Done.")

print("Logging into database...")
try:
    conn = toolforge.connect(databasename, user=forgeUsername, password=forgePassword)
except Exception as e:
    print("Error: {}".format(e))
    sys.exit(0)
# https://wikitech.wikimedia.org/wiki/User:Legoktm/toolforge_library

gaStats = []

statsText = site.Pages["User:GA bot/Stats"].text()
statsArray = statsText.splitlines()

for statPerson in statsArray:
    name = re.search(r'\[\[User:(.+?)\|.+?\]\]', statPerson, re.I).group(1)
    reviews = re.search(r'<td>\s*(\d+)\s*<\/td>', statPerson, re.I).group(1)
    dictAdd = {"name":name, "reviews":reviews}
    gaStats.append(dictAdd.copy())
        
page = site.Pages["User:GA bot/Don't notify users for me"]
user_no_msg_regex = re.compile(r'\[\[User:(.+)\]\]', re.IGNORECASE)
dontNotify = user_no_msg_regex.findall(page.text())
transcludes = getTransclusions(site, "Template:GA nominee")
if len(transcludes) < 1:
    print("No transclusions found.\n")
    sys.exit(0)
print("Done.")
articles = []

for trans in transcludes:
    if re.search(r'^Talk:', trans):
        articles.append(trans)
        print("Appended article")
del trans  # variable no longer needed

wpgan = site.Pages["Wikipedia:Good article nominations"]
text = wpgan.text()
if text is "":
    print("[[Wikipedia:Good article nominations]] is empty.\n")
    sys.exit(0)

# Each GA nominee tag will now be standardized and stripped apart, with each detail found in each tag sorted into the right array

titles = []

# Change variable names (important)

ganoms = []
count = 0
for art in articles:
    title = art[5:]
    articlePage = site.Pages[art]
    contents = articlePage.text()
    if not contents:
        continue
    ganom = None
    code = mwparserfromhell.parse(contents)
    for template in code.filter_templates():
        if template.name.matches("GA nominee") or template.name.matches("GAnominee"):
            ganom = template
            break
    if ganom is None:
        continue  # move on

    currentNom = GANom(title, ganom)
    reviewpage = "{}/GA{}".format(art, currentNom.reviewpage)
    reviewpage_content = site.Pages[reviewpage].text()
    reviewer = re.search(r"'''Reviewer:''' .*?(\[\[User:([^|]+)\|[^\]]+\]\]).*?\(UTC\)", reviewpage_content)

    if reviewer:
        currentNom.set_reviewer(reviewer.group(2), reviewer[0].replace("'''Reviewer:''' ", ''))
        if currentNom.status is 'new':
            currentNom.set_status('on review')
            old_contents = contents
            contents = contents.replace("status=|", "status=onreview|")
            if not re.search('\{\{' + re.escape(reviewpage) + '\}\}', contents, re.IGNORECASE):
                contents += "\n\n{{{" + reviewpage + "}}}"
            if (contents is not old_contents and allow_bots(art.text(), botuser)) is True:
                articlePage.save(contents, summary="Transcluding GA review", bot=True, minor=True)

            # Notify the nominator that the page is now on review
            noms_talk_page = site.Pages["User talk:" + currentNom.nominator_plain].resolve_redirect()
            # Clean all this up
            if (noms_talk_page[0:len("User talk")] is "User talk" and not
            re.search(r'\[\[{}\]\].+?{}/'.format(re.escape(currentNom), re.escape('<!-- Template:GANotice -->')),
            noms_talk_page.content())
            and not currentNom.reviewer in dontNotify):
                sig = currentNom.reviewer
                sig2 = "-- {{subst:user0|User=" + sig + "}}"
                msg = "{{subst:GANotice|article=" + currentNom + "|days=7}} <small>Message delivered by [[User:" + botuser + "|" + botuser + "]], on behalf of [[User:" + sig + "|" + sig + "]]</small>" + sig2
                if allow_bots(noms_talk_page.content(), botuser):
                    noms_talk_page.save(noms_talk_page.content() + "\n\n" + msg,
                              summary="/* Your [[WP:GA|GA]] nomination of [[" + currentNom + "]] */ new section")

            del old_contents

            with conn.cursor() as cur:
                cur.execute("DELETE FROM `gan` WHERE `page` = {};".format(title)) # If already defined
                cur.execute("INSERT INTO `gan` (`page`, `reviewerplain`, `reviewer`, `subtopic`, "
                            "`nominator`) VALUES ({},{},{},{},{});".format(title, currentNom.reviewer,
                                                                          reviewer[1], currentNom.subtopic,
                                                                          currentNom.nominator_plain))
                cur.execute("INSERT INTO `reviews` (`review_article`, `review_subpage`, "
                            "`review_user`, `review_timestamp`) VALUES "
                            "({},{},{},{});".format(site.Pages[title].pageid, site.Pages[reviewpage].pageid,
                                                   getUserID(currentNom.reviewer),
                                                   currentNom.unixtime))
                cur.execute("INSERT INTO `user` (`user_id`, `user_name`) VALUES ({},{});".format(
                    getUserID(currentNom.reviewer),
                    currentNom.reviewer))
                cur.execute("INSERT INTO `article` (`article_id`, `article_title`, `article_status`) "
                            "VALUES ({},{},{});".format(site.Pages[title].pageid, title, ""))
            alreadyThere = False
            nameFound = next((item for item in gaStats if item["name"] == currentNom.reviewer), False)
            if nameFound:
                nameFound["reviews"] += 1
                alreadyThere = True
            if not alreadyThere:
                dictAdd = {"name":currentNom.reviewer, "reviews":"1"}
                gaStats.append(dictAdd.copy())
                
    if currentNom.wikicode() not in gantext and currentNom.status == 'on hold':
        talktitle = "User talk:{}".format(currentNom.nominator_plain)
        noms_talk_page = site.Pages[talktitle].resolve_redirect()
        nomtalkText = noms_talk_page.text()

        templateExists = re.search('\[\[{}\]\].+?<!-- Template:GANotice result=' \
                                   'hold -->'.format(re.escape(title)),
                                   nomtalkText, re.I)
        sig = currentNom.reviewer
        templateExists = None

        if (talktitle[:9] == "User talk" and not templateExists and
            sig not in dontNotify and allow_bots(nomtalkText, botuser)):

                finalsig = "-- {{{{subst:user0|User={}}}}} ~~~~~".format(sig)
                message = "{{{{subst:GANotice|article={0}|result=hold}}}} " \
                          "<small>Message delivered by [[User:{1}|" \
                          "{1}]], on behalf of [[User:{2}|{2}]]</small> " \
                          "{3}".format(title, botuser, sig, finalsig)

                noms_talk_page.save('\n\n{}'.format(message), '/* Your [[WP:GA|GA]] nomination of ' \
                                                                  '[[{}]] */ new section'.format(title))
                

rows = []
with conn.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute("SELECT * FROM `gan`;")
    rows = cur.fetchall()

for row in rows:
    if row['page'] in titles:
        continue

    status = None
    addTemplate = False

    contents = site.Pages["Talk:{}".format(row['page'])].text()

    statusGA = re.search(r'\|\s*?currentstatus\s*?=\s*?GA', contents, re.I)
    isGA = re.search(r'\{{2}\s?GA(?! nominee)', contents)
    failedGA = re.search(r'\{{2}\s?FailedGA', contents, re.I)

    noms_talk_page = site.Pages["User talk:{}".format(row['nominator'])].resolve_redirects()
    nomtalkText = noms_talk_page.text()
    templateExists = re.search('\[\[{}\]\].+?<!-- Template:GANotice result=' \
                               '(?:pass|fail) -->'.format(re.escape(row['page'])),
                               nomtalkText, re.I)

    sig = row['reviewerplain']
    fullsig = "-- {{subst:user0|User={}}} ~~~~~".format(sig)
    
    summary = "/* Your [[WP:GA|GA]] nomination of " \
              "[[{}]] */ new section".format(row['page'])
    
    if (noms_talk_page[:9] == "User talk" and not templateExists and
        sig not in dontNotify and allow_bots(nomtalkText, botuser)):
        addTemplate = True
    
    if statusGA or isGA and not failedGA:        
        add_icon(row['page'])

        if addTemplate:
            message = "{{subst:GANotice|article={0}|result=pass}} " \
                      "<small>Message delivered by [[User:{1}|" \
                      "{1}]], on behalf of [[User:{2}|{2}]]</small> " \
                      "{3}".format(row['page'], botuser, sig, fullsig)
            noms_talk_page.save("\n\n{}".format(message), summary)
    else:
        if addTemplate:
            message = "{{subst:GANotice|article={0}|result=fail}} " \
                      "<small>Message delivered by [[User:{1}|" \
                      "{1}]], on behalf of [[User:{2}|{2}]]</small> " \
                      "{3}".format(row['page'], botuser, sig, fullsig)
            noms_talk_page.save("\n\n{}".format(message), summary)
            
    with conn.cursor() as cur:
        cur.execute("DELETE FROM `gan` WHERE `page` = {};".format(row['page']))
        
ganoms.sort(reverse=True) # Sort from most recent (?)

# Better variable names
lines = text.splitlines()

newpage = ""

subcat = None

for line in lines:
    if subcat is None:
        subtopic = re.search(r'<!--\s*Bot\s*Start\s*"([^"]+)"\s*-->', line, re.I)
        if subtopic:
            subcat = subtopic.group(1)
        newpage += "{}\n".format(line)

    elif line.find('<!-- Bot End -->') != -1:
        for nom in ganoms:
            if nom.subtopic == subcat:
                newpage += nom.wikicode()
        newpage += "{}\n".format(line)
        subcat = None

site.Pages["Wikipedia:Good article nominations"].save(newpage, "Update nominations page",
                                                      minor=False, bot=True)

splitPage = newpage.split('<!-- EVERYTHING BELOW THIS COMMENT IS UPDATED ' \
                          'AUTOMATICALLY BY A BOT -->')
splitPage2 = splitPage[1].split('<!-- EVERYTHING ABOVE THIS COMMENT IS UPDATED ' \
                                'AUTOMATICALLY BY A BOT -->')
lines = splitPage2[0].splitlines()

topicLists = {}

for line in lines:
    subTopic = re.search(r'^\s*==([^=]+)==\s*$', line)
    if subTopic:
        subcat = subTopic.group(1).strip()
    if subcat:
        topicLists[subcat] += "{}\n".format(line)

for subcat, content in topicLists.items():
    startPage = site.Pages["Wikipedia:Good article nominations/Topic lists/" \
                           "{}".format(subcat)]
    startText = startPage.text()
    tempSplit = startText.split('<!-- BOT STARTS HERE -->')
    content = "{}<!-- BOT STARTS HERE -->\n{}".format(tempSplit[0], content)

    subcats = re.findall(r'<!--\s*Bot\s*Start\s*"([^"]+)"\s*-->', startText,
                         re.I)
    startPage.save(content, "Update subtopic list")

# Really dislike all this temporary looping stuff. Should be changed

statsLength = len(gaStats)
while statsLength > 0:
    newStats = 0
    dummyNum = 1 # Replace this?
    while dummyNum < statsLength:
        if gaStats[dummyNum - 1]['reviews'] < gaStats[dummyNum]['reviews']:
            tmp = gaStats[dummyNum]
            gaStats[dummyNum] = gaStats[dummyNum - 1]
            gaStats[dummyNum - 1] = tmp
            newStats = dummyNum
            dummyNum += 1
    statsLength = newStats

content = "<table class=\"wikitable\">\n<tr><th>User</th><th>Reviews</th></tr>\n"
for gaStat in gaStats:
    user = gaStat["name"]
    reviews = gaStats["reviews"]
    content += "<tr> <td> [[:User:{}]] </td> <td> {} </td> </tr>\n".format(user, reviews)
content += "</table>\n"
site.Pages["User:GA bot/Stats"].save(content, "Update Stats (Bot)")
