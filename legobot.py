#!/usr/bin/env python3.6
import mwparserfromhell
import toolforge
import mwclient  # TODO: clean up mwclient imports
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


def place_notif(user, status, page):
    if user is None:
        raise ValueError("Name can't be None")
    if status is None:
        raise ValueError("Status can't be None")
    if page is None:
        raise ValueError("Page can't be None")


# some code


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


def update_GAN_page():
    pass


def transclude_review():
    pass


def add_icon():
    pass


def getTransclusions(site, page, sleep_duration=None, extra=""):
    cont = None
    pages = []
    i = 0
    while True:
        result = site.api('query', list='embeddedin', eititle=str(page), eicontinue=cont, eilimit=500, format='json')
        print("got here")
        if sleep_duration is (not None):
            time.sleep(sleep_duration)
        # res2 = result['query']['embeddedin']
        for res in result['query']['embeddedin']:
            print('append')
            pages.append(str(i) + " " + res['title'])
            i += 1
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


class editsummary:
    def __init__(self):
        self.passed = {}
        self.failed = {}
        self.sNew = {}
        self.onReview = {}
        self.onHold = {}

    def passed(self, page, subcat):
        # self.passed.append(page)
        self.passed[subcat] = page
        pass  # TODO: Fix

    def failed(self, page, subcat):
        # self.failed.append(page)
        self.failed[subcat] = page
        pass  # TODO: Fix

    def sNew(self, page, subcat):
        self.sNew[subcat] = page

    def onReview(self, page, subcat, reviewer):
        self.onReview[subcat] = [page, reviewer]

    def onHold(self, page, subcat, reviewer):
        self.onHold[subcat] = [page, reviewer]

    def rmSubCats(self, var, subcats=False):
        clean = []
        # TODO: Complete
        pass

    def generate(self, subcats=False):
        sum = ''
        if self.sNew:
            # TODO: complete
            pass
        pass


class GANom:
    def __init__(self, article):
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
        self.article = article.trim()

    def toString(self):
        return self.article

    def getVar(self, var):
        if var in ['status', 'reviewpage', 'reviewer', 'subtopic', 'unixtime', 'subtopic', 'nominator',
                   'nominator_plain']:
            return var
        return False

    def parse_template(self, template):
        if template.has("1"):  # timestamp
            self.timestamp = template.get("1").value.strip()
            self.set_time(template.get("1").value)
        if template.has("nominator"):  # nominator
            pass
        if template.has("page"):  # page
            self.set_review_page(template.get("page").value)
            pass
        if template.has("status"):  # status
            self.set_status(template.get("status").value)
            pass
        if template.has("subtopic"):  # subtopic
            self.set_subtopic(template.get("subtopic").value)
            pass
        if template.has("note"):  # note
            self.set_note(template.get("note").value)
            pass
        if template.has("time"):  # time
            pass
        pass

    def set_time(self, timestamp):
        # TODO: work on
        unix = parse(timestamp).strftime(date_format)
        if unix is False:
            return False
        self.unixtime = unix
        # unix = datetime.strptime(timestamp, '%m/%d/%Y')
        pass

    def set_review_page(self, page):
        page = page.split()
        if re.match(r'/^[0-9]+$/', page):
            self.reviewpage = page

    def set_subtopic(self, topic):
        topic = topic.replace(topic, ", and", " and").strip()
        if not (not topic):
            self.subtopic = topic

    def set_status(self, status):
        pass

    def cleanStatus(self, status):
        if (re.match(r'/(on ?)?hold/i', status)):
            return 'on hold'
        elif (re.match(r'/(on ?)?review/i', status)):
            return 'on review'
        elif (re.match(r'/(2nd|second|2)? ?op(inion)?/i', status)):
            return '2nd opinion'
        return status

    def set_nominator(self, nominator):
        nominator = nominator.strip()
        if nominator(not None):
            self.nominator = nominator
            m = re.match(r"/\[\[User:(.+?)\|.+?\]\]/", nominator)
            if m.group(1) is (not None):
                # TODO: fix/work on
                nom = m.group(1).replace('_', ' ')
                nom = nominator[0].upper() + nominator[1:]
                # nom = m.group(1)
                # nom = m.replace('_',' ')

                nom = nominator[0].upper() + nominator[1:]
                self.nominator_plain = nom  # nominator[0].upper() + nominator[1:]

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

    def num_of_reviewers(self, name):
        global gaStats

    # TODO: for gaStats in
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
# TODO: Log in stuff
print("Checking users how don't want messages left on their behalf...")
site = mwclient.Site(('https', 'en.wikipedia.org'), '/w/')

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
# https://wikitech.wikimedia.org/wiki/User:Legoktm/toolforge_library

page = site.Pages["User:GA bot/Don't notify users for me"]
user_no_msg_regex = re.compile(r'\[\[User:(.+)\]\]', re.IGNORECASE)
dontNotify = user_no_msg_regex.findall(page.text())
transcludes = getTransclusions(site, "Template:GA nominee")
if len(transcludes) < 1:
    print("No transclusions found.\n")
    sys.exit(0)
print("Done.")
articles = []
trans_check = re.compile(r'^Talk:')
for trans in transcludes:
    if trans_check.match(trans):
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
ganoms = []
count = 0
for art in articles:
    title = art[5:]
    contents = site.Pages[art]
    if not contents:
        continue
    ganom = None
    code = mwparserfromhell.parse(text)
    for template in code.filter_templates():
        if template.name.matches("ga nominee") or template.name.matches("ganominee"):
            ganom = template
            break
    if ganom is None:
        continue  # move on

    # TODO: The next block of code, could probably be done better
    currentNom = GANom(title, ganom)
    reviewpage = "Talk:" + currentNom + "/GA" + currentNom.getVar('reviewpage')
    reviewpage_content = site.Pages[reviewpage]
    reviewer = re.match(r"'''Reviewer:''' .*?(\[\[User:([^|]+)\|[^\]]+\]\]).*?\(UTC\)", reviewpage_content)
    # if re.match(r"'''Reviewer:''' .*?(\[\[User:([^|]+)\|[^\]]+\]\]).*?\(UTC\)",reviewpage_content)
    if reviewer:
        currentNom.set_reviewer(reviewer.group(2), reviewer[0].replace("'''Reviewer:''' ", ''))
        if currentNom.getVar('status') is 'new':
            currentNom.set_status('on review')
            old_contents = contents
            contents = contents.replace("status=|", "status=onreview|")
            if not re.match('\{\{' + re.escape(reviewpage) + '\}\}', contents, re.IGNORECASE):
                contents += "\n\n{{{" + reviewpage + "}}}"
            if (contents is not old_contents and allow_bots(art.text(), 'GA bot')) is True:
                page.save(art, summary="Transcluding GA review", bot=True, minor=True)

            # Notify the nom that the page is now on review
            noms_talk_page = site.Pages["User talk:" + currentNom.getVar('nominator_plain')]
            # FIXME: noms_talk_page.resolveRedirects() http://mwclient.readthedocs.io/en/latest/reference/page.html?highlight=redirect
            # Clean all this up
            if (noms_talk_page[0:len("User talk")] is "User talk" and not
            re.match(r'\[\[{}\]\].+?{}/'.format(re.escape(currentNom), re.escape('<!-- Template:GANotice -->')),
            noms_talk_page.content())
            and not currentNom.getVar('reviewer') in dontNotify):
                sig = currentNom.getVar('reviewer')
                sig2 = "-- {{subst:user0|User=" + sig + "}}"
                msg = "{{subst:GANotice|article=" + currentNom + "|days=7}} <small>Message delivered by [[User:" + botuser + "|" + botuser + "]], on behalf of [[User:" + sig + "|" + sig + "]]</small>" + sig2
                if allow_bots(noms_talk_page.content(), 'GA bot'):
                    page.save(noms_talk_page.content() + "\n\n" + msg,
                              summary="/* Your [[WP:GA|GA]] nomination of [[" + currentNom + "]] */ new section")

            del old_contents

            with conn.cursor() as cur:
                cur.execute("DELETE FROM `gan` WHERE `page` = {}".format(title))
                cur.execute("INSERT INTO `gan` (`page`, `reviewerplain`, `reviewer`, `subtopic`, "
                            "`nominator`) VALUES ({},{},{},{},{})".format(title, currentNom.getVar('reviewer'),
                                                                          reviewer[1], currentNom.getVar('subtopic'),
                                                                          currentNom.getVar('nominator_plain')))
                cur.execute("INSERT INTO `reviews` (`review_article`, `review_subpage`, "
                            "`review_user`, `review_timestamp`) VALUES "
                            "({},{},{},{})".format(site.Pages[title].pageid, site.Pages[reviewpage].pageid,
                                                   getUserID(currentNom.getVar('reviewer')),
                                                   currentNom.getVar('unixtime')))
                cur.execute("INSERT INTO `user` (`user_id`, `user_name`) VALUES ({},{})".format(
                    getUserID(currentNom.getVar('reviewer')),
                    currentNom.getVar('reviewer')))
                cur.execute("INSERT INTO `article` (`article_id`, `article_title`, `article_status`) "
                            "VALUES ({},{},{})".format(site.Pages[title].pageid, title, ""))
