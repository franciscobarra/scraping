from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
import re
import json
from fastapi import FastAPI
import mysql.connector
import time
import hashlib
import spacy
from selenium import webdriver
from time import sleep
from random import *
from threading import *
import threading

#PATH = "./chromedriver_linux64/chromedriver"
PATH = "./chromedriver_win32/chromedriver"
chrome_options = Options()  
chrome_options.add_argument("--headless") # Opens the browser up in background
#chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument("--disable-setuid-sandbox")
#chrome_options.add_argument('--disable-dev-shm-usage')    

Urls = [
    "notebook",
    "iphone",
    "smart-tv"
]


Urls_ = [
    "notebook",
    "iphone",
    "celular",
    "parka",
    "doite",
    "lippi",
    "casaca",
    "smart-tv",
    "chaqueta"
]



nlp = spacy.load("es_core_news_sm")

def normalize(text):
    doc = nlp(text)
    words = [t.orth_ for t in doc if not t.is_punct | t.is_stop]
    lexical_tokens = [t.lower() for t in words]
    return "-".join(map(str, lexical_tokens))

def hashing(text):
    hash_object = hashlib.md5(text.encode())
    return hash_object.hexdigest()


#PATH = "./chromedriver_linux64/chromedriver"
PATH = "./chromedriver_win32/chromedriver"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class product: 
        def __init__(self, tittle, origprice, sellprice, percent, url): 
            self.tittle = tittle 
            self.origprice = origprice
            self.sellprice = sellprice
            self.percent = percent
            self.url  = url 
aProducts = list()
#chrome_options = Options()  
#chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument("--disable-setuid-sandbox")
#chrome_options.add_argument('--disable-dev-shm-usage')    
app = FastAPI()



@app.get("/api")
def read_root():
    print("F")

    aProducts = list()
    mycursor.execute("SELECT title, origprice, sellprice, percentdiscount, url FROM products order by percentdiscount desc")

    for x in mycursor:
        aProducts.append(product(x[0], x[1], x[2], x[3], x[4]))

    return aProducts

@app.get("/search/{obj}")
def search_products(obj, conn, cur):

    url = "https://www.falabella.com/falabella-cl/search?Ntt="+obj

    with Chrome(options=chrome_options,executable_path=PATH) as browser:
        browser.get(url)
        html = browser.page_source

    sp = BeautifulSoup(html, 'html.parser')  
    pUri = sp.find_all('meta',{'property' : 'og:url'})
    urlPrin = pUri[0]["content"]
    if urlPrin == "/falabella-cl/search/":
        urlPrin = url+"&page=" 
    else:
        urlPrin= urlPrin+"?page="
    aProducts = list()

    for nPage in range(1,50): 
        url = urlPrin+str(nPage)
        print(bcolors.OKBLUE + url + bcolors.ENDC)
        print(url)
        with Chrome(options=chrome_options,executable_path=PATH) as browser:
            browser.get(url)
            html = browser.page_source

        sp = BeautifulSoup(html, 'html.parser')
        title = sp.find_all()
        test = sp.find_all('b')
        uri = ""
        if bool(test):
            for x in title :
                for attr in x.attrs:
                    if x.name == 'a' and attr == 'href' and 'https://www.falabella.com' in x[attr]:
                        uri = x["href"]
                    if x.name == 'b' and attr == 'id' and 'displaySubTitle' in x[attr]:
                        tittle = x.text
                    if x.name == 'li' and attr == 'class' and 'prices-0' in x[attr]:
                        sellprice = ''
                        percent = ''
                        for st in x.text.split(" "):
                            if sellprice != '' and bool(re.search(r'\d', st)) : percent = st.strip().replace("%", "").replace("-","").replace(" ","")
                            if sellprice == '' and bool(re.search(r'\d', st)) : sellprice = st.strip().replace("$", "").replace(".","").replace(" ","")

                    if x.name == 'li' and attr == 'class' and 'prices-1' in x[attr]:
                        origprice = x.text.strip().replace("$", "").replace(".","").replace(" ","")
                        #origprice = origprice[0 : origprice.index("-")]
                        origprice = re.sub("-", '', origprice)
                        aProducts.append(product(tittle, origprice, sellprice, percent, uri))
                        break
        else: break

        cur = conn.cursor()

        for p in aProducts:
            lemantitle = normalize(p.tittle)
            cur.callproc('storeProducts', [p.tittle, str(lemantitle), hashing(str(lemantitle)+str(p.origprice)+str(p.sellprice)), p.origprice, p.sellprice, "0" if p.percent == "" else p.percent, p.url,"Falabella", obj, "Ni idea"])
            
        cur.close() 

        aProducts = list()
        
    
class MultiScan(threading.Thread):

    def __init__(self, conn, cur, name):
        threading.Thread.__init__(self)
        self.conn = conn
        self.cur = cur
        self.name = name

    def run(self):
        search_products(self.name, self.conn, self.cur)

for i in Urls:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="scrap",
        connection_timeout=28800
    )

    cur = conn.cursor()
    MultiScan(conn, cur, i).start()  


# Pendiente: 
# - Integrar precio de tienda
# - Integrar framework FrondEnd
# - Regularizar Docker
