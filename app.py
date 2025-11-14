from flask import Flask,render_template,request,redirect,url_for
from jinja2 import Environment,FileSystemLoader,select_autoescape
import sqlite3
import random
import logging
from functools import wraps
from collections import OrderedDict
import re
import qrcode
import io, base64

logger = logging.getLogger(__name__)
logging.basicConfig(filename='app.log', encoding='utf-8', level=logging.DEBUG,format='%(asctime)s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

con = sqlite3.connect("url.db")
cur=con.cursor()
cur.execute("""create table if not exists Aliassen(
            Alias text primary key,
            Url text
            )""")
cur.close()

app = Flask(__name__)

@app.route("/alias_toevoegen", methods=["POST"])
def alias_toevoegen():
    logger.info('Visited /alias_toevoegen')
    try:
        alias=""
        for getal in range(15):
            keuze=random.choice([
            chr(random.randint(48,57)),
            chr(random.randint(65,90)),
            chr(random.randint(97,122))
            ])
            alias+=keuze

        url= request.form["alias"]
        if url=="":
            logger.info('Geen Url ingegeven')
            foutmelding="Er heeft zich een fout voor gedaan.\n Gelieve een url in te geven.\nMet de vorm 'https://example.com'"
            return render_template("formulier.html",foutmelding=foutmelding)
        test = re.search(r"https?://[a-zA-Z0-9.]+\.[a-zA-Z]{2,}",url)
        if test:
            con = sqlite3.connect("url.db")
            cur=con.cursor()
            cur.execute("select Url from Aliassen where Url=?",(url,))
            al_toegevoegd=cur.fetchall()
            logger.info(f'Url gekrieërd: {url}')
            if al_toegevoegd:
                logger.info('Url proberen te maken die al bestaat')
                raise Exception()
        else:
            foutmelding="Gelieve een geldige url in te geven.\nMet de vorm 'https://example.com'"
            return render_template("formulier.html",foutmelding=foutmelding)
            
        cur.execute("insert into Aliassen values(?,?)",(alias,url))
        con.commit()
        con.close()
        return render_template("template_6.html",alias=alias,url=url)
    except:
        foutmelding="Er heeft zich een fout voor gedaan.\n Gelieve een url in te geven die nog niet in het systeem zit."
        return render_template("404_pagina.html",foutmelding=foutmelding)


@app.route("/")
def home():
    logger.info('home pagina bezocht')
    con = sqlite3.connect("url.db")
    cur=con.cursor()
    cur.execute("select Alias,Url from Aliassen")
    rows=cur.fetchall()
    con.close()
    qrcodes=[]
    samen={}
    for alias,url in rows:
        img=qrcode.make(url)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        qrcodes.append(img_base64)
    getal=0
    for alias,url in rows:
        samen[url]=qrcodes[getal]
        getal+=1
    return render_template("homepage.html", samen=samen)
@app.route("/shorturl/<link>")
def shorturl(link):
    url = get_url_from_db(link)   # door de decorator zit hier caching op
    if url:
        logger.info(f'gebruiker bezocht short url: {url}')
        return redirect(url)
    else:
        return render_template("fout_pagina.html")
    
@app.route("/input")
def input():
    logger.info('gebruiker heeft /input bezocht')
    return render_template("formulier.html")

def remember_recent_calls(func):
    cache = OrderedDict()

    @wraps(func)
    def wrapper(arg):
        # zit arg in cache? meteen teruggeven
        if arg in cache:
            return cache[arg]

        # anders: resultaat berekenen
        result = func(arg)

        # indien cache vol (5 items), oudste weggooien
        if len(cache) == 5:
            cache.popitem(last=False)

        # nieuw resultaat toevoegen aan cache
        cache[arg] = result
        return result

    return wrapper
def get_url_from_db(alias):
    con = sqlite3.connect("url.db")
    cur = con.cursor()
    cur.execute("select Url from Aliassen where Alias=?", (alias,))
    row = cur.fetchone()
    con.close()
    if row:
        return row[0]   # de echte url
    return None
    

if __name__ == "__main__":
    logger.debug('applicatie gestart')
    app.run(debug=True)