from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError
import re
from geopy.geocoders import Nominatim
import pycountry_convert as pc
from transformers import BartTokenizer, BartForConditionalGeneration
from flask_ngrok import run_with_ngrok
from pyngrok import ngrok
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report
folds = StratifiedKFold(n_splits=150)
import numpy as np
#import pandas as pd

from flask import Flask, render_template, request, jsonify


app = Flask(__name__)
#run_with_ngrok(app)
#port_no = 5000
#ngrok.set_auth_token("2Lv3HZnzV3E5TiSU9xdeAm1toHa_2AB2g8dXp8cQSp6z8Yrym")
#url = ngrok.connect(port_no).api_url


# **************************************************************************************************************
#                    ***************************Main Body*****************************
# **************************************************************************************************************
listp=[]
@app.route('/')
def starting():
    return "Ez Newspaper"


@app.route('/latest', methods=['GET'])
def TopNewsHndL():
    l = TopNewsLinks()
    newhead = {}
    i=0
    
    for key,link in l.items():
        try:
            item = urlopen(link)
            print(link)
        except HTTPError as e:
            print(e)
        except URLError as e:
            print(e)
        try:
            bs = BeautifulSoup(item,'html.parser')
            for head in bs.find_all('h1'):
                newhead["Heading"+str(i)]=head.text
                i+=1
        except AttributeError as e:
            print(e)
    
    list = {
        "TrendingHeadings":[newhead,l] }

    return jsonify(list)




@app.route("/TrendingNewsHndL", methods=["GET"])
def TrendingNewsHndL():
    l = TrendingNewsLinks()
    newhead = {}
    i=0
    
    for key,link in l.items():
        try:
            item = urlopen(link)
            print(link)
        except HTTPError as e:
            print(e)
        except URLError as e:
            print(e)
        try:
            bs = BeautifulSoup(item,'html.parser')
            for head in bs.find_all('h1'):
                newhead["Heading"+str(i)]=head.text
                i+=1
        except AttributeError as e:
            print(e)
    
    list = {
        "TrendingHeadings":[newhead,l] }

    return jsonify(list)


@app.route("/paragraph", methods=['POST'])
def Get_para():
    paragraph = []
    paragraphs = []
    Newspara = []
    Newsparagraph = {}
    get_url = request.json['Url']

    if str(get_url).startswith("https://www.bbc.com/"):
        if str(get_url).startswith("https://www.bbc.com/news/live/"):
            html = urlopen(get_url)
            bsObj = BeautifulSoup(html)
            for para in bsObj.find("section", {'class': 'qa-summary-points'}).find_all('li'):
                paragraph.append(para.text)
            paragraphs = " ".join(paragraph)
            Newspara.append(paragraphs)
            listp.append(bsObj.find('h1').text)
        else:
            html = urlopen(get_url)
            bsObj = BeautifulSoup(html)
            for para in bsObj.find_all('div', attrs={'data-component': 'text-block'}):
                paragraph.append(para.text)
            paragraphs = " ".join(paragraph)
            Newspara.append(paragraphs)
            listp.append(bsObj.find('h1').text)
            print("BBC")
    elif str(get_url).startswith("https://www.aljazeera.com/"):
        if str(get_url).startswith("https://www.aljazeera.com/news/liveblog"):
            html = urlopen(get_url)
            bsObj = BeautifulSoup(html)
            for para in bsObj.find('div', {'class': 'article-header'}).find('h1'):
                # print(para.text)
                paragraph.append(para.text)
            paragraphs = " ".join(paragraph)
            Newspara.append(paragraphs)
            listp.append(bsObj.find('h1').text)
        else:
            html = urlopen(get_url)
            bsObj = BeautifulSoup(html)
            for para in bsObj.find_all('div', {'class': 'wysiwyg--all-content'}):
                # print(para.text)
                paragraph.append(para.text)
            paragraphs = " ".join(paragraph)
            Newspara.append(paragraphs)
            listp.append(bsObj.find('h1').text)
        print("AJ")
    
    elif str(get_url).startswith("https://edition.cnn.com/"):
        ma = find_match(get_url)
        if ma == 1:
            #print("match found") 
            html = urlopen(get_url)
            bsObj = BeautifulSoup(html)
            for para in bsObj.find('ul',{'class':'cnn_rich_text'}).find_all('li'):
                paragraph.append(para.text)
            paragraphs = " ".join(paragraph)
            Newspara.append(paragraphs)
            listp.append(bsObj.find('h1').text) 
            
        else :
            #print("match not found")
            html = urlopen(get_url)
            bsObj = BeautifulSoup(html)
            for para in bsObj.find('div',{'class':'article__content'}).find_all('p'):
                paragraph.append(para.text)
            paragraphs = " ".join(paragraph)
            Newspara.append(paragraphs)
            listp.append(bsObj.find('h1').text)
        print("CNN")
    
    else:
        html = urlopen(get_url)
        bsObj = BeautifulSoup(html)
        for para in bsObj.find('section',{'class':'content__body'}).find_all('p'):
            paragraph.append(para.text)
        paragraphs = " ".join(paragraph)
        Newspara.append(paragraphs)
        listp.append(bsObj.find('h1').text)
        print("CBS")


    print(listp)
    Newsparagraph = {"Paragraph":Newspara}

    return jsonify(Newsparagraph)


@app.route('/summary', methods=['POST'])
def get_summary():
    get_url =request.json['Url']
    paragraph = []

    model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')
    tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')

    if str(get_url).startswith("https://www.bbc.com/"):
        html = urlopen(get_url)
        bsObj = BeautifulSoup(html)
        for para in bsObj.find_all('div', attrs={'data-component': 'text-block'}):
            paragraph.append(para.text)
        paragraphs = " ".join(paragraph)
        print("BBC")
    elif str(get_url).startswith("https://www.aljazeera.com/"):
        if str(get_url).startswith("https://www.aljazeera.com/news/liveblog"):
            html = urlopen(get_url)
            bsObj = BeautifulSoup(html)
            for para in bsObj.find('div', {'class': 'article-header'}).find('h1'):
                # print(para.text)
                paragraph.append(para.text)
            paragraphs = " ".join(paragraph)
        else:
            html = urlopen(get_url)
            bsObj = BeautifulSoup(html)
            for para in bsObj.find_all('div', {'class': 'wysiwyg--all-content'}):
                # print(para.text)
                paragraph.append(para.text)
            paragraphs = " ".join(paragraph)
        print("AJ")
    
    elif str(get_url).startswith("https://edition.cnn.com/") :
        ma = find_match(get_url)
        if ma == 1:
            #print("match found") 
            html = urlopen(get_url)
            bsObj = BeautifulSoup(html)
            for para in bsObj.find('ul',{'class':'cnn_rich_text'}).find_all('li'):
                paragraph.append(para.text)
            paragraphs = " ".join(paragraph)
            
        else :
            #print("match not found")
            html = urlopen(get_url)
            bsObj = BeautifulSoup(html)
            for para in bsObj.find('div',{'class':'article__content'}).find_all('p'):
                paragraph.append(para.text)
            paragraphs = " ".join(paragraph)
        print("CNN")
    
    else:
        html = urlopen(get_url)
        bsObj = BeautifulSoup(html)
        for para in bsObj.find('section',{'class':'content__body'}).find_all('p'):
            paragraph.append(para.text)
        paragraphs = " ".join(paragraph)
        print("CBS")

    tokens = tokenizer(paragraphs, truncation=True, padding=True, return_tensors='pt')
    predict = model.generate(tokens['input_ids'], max_length=300, min_length=30)
    summary = [tokenizer.decode(g, skip_special_tokens=True) for g in predict]

    return jsonify({"Summary": summary})


@app.route('/location_based_bbc', methods=['POST'])
def location_based_news_bbc():
    i=0
    newhead = {}
    Latitude = request.json['lat']
    Longitude = request.json['lon']
    
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.reverse(Latitude+","+Longitude,language='en')
    #print("\nLocation of the given Latitude and Longitude:")
    #print(location)
    
    address = location.raw['address']
    #print("Address:",address)
    
    country = address.get('country', '')
    country_code  = address.get('country_code','')
    #print('Country:',country)
    
    country_alpha2 = pc.country_name_to_country_alpha2(country)
    country_continent_code = pc.country_alpha2_to_continent_code(country_alpha2)
    country_continent_name = pc.convert_continent_code_to_continent_name(country_continent_code)
    
    cnn = country_continent_name.lower()
    
    links = BBC_Location_Links(cnn)
    
    for key,item in links.items():
        l = urlopen(item)  
        bsobj = BeautifulSoup(l)
        for head in bsobj.find_all('h1'):
                newhead["Heading" + str(i)]=head.text 
                i+=1
    list = {
        "LocationBased":[newhead,links]
    }

    return jsonify(list)

@app.route('/location_based_ajzeera', methods=['POST'])
def location_based_news_aljazeera():
    i=0
    newhead = {}
    Latitude = request.json['lat']
    Longitude = request.json['lon']
    
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.reverse(Latitude+","+Longitude,language='en')
    #print("\nLocation of the given Latitude and Longitude:")
    #print(location)
    
    address = location.raw['address']
    #print("Address:",address)
    
    country = address.get('country', '')
    country_code  = address.get('country_code','')
    #print('Country:',country)
    
    country_alpha2 = pc.country_name_to_country_alpha2(country)
    country_continent_code = pc.country_alpha2_to_continent_code(country_alpha2)
    country_continent_name = pc.convert_continent_code_to_continent_name(country_continent_code)
    
    cnn = country_continent_name.lower()
    
    links = Aljazira_Location_links(cnn)
    
    for key,item in links.items():
        l = urlopen(item)  
        bsobj = BeautifulSoup(l)
        for head in bsobj.find_all('h1'):
                newhead["Heading"+str(i)]=head.text 
                i+=1
    
   
    list = {
        "LocationBased":[newhead,links]
    }

    return jsonify(list)

@app.route('/location_based_cnn', methods=['POST'])
def location_based_news_cnn():
    i=0
    newhead = {}
    Latitude = request.json['lat']
    Longitude = request.json['lon']
    
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.reverse(Latitude+","+Longitude,language='en')
    #print("\nLocation of the given Latitude and Longitude:")
    #print(location)
    
    address = location.raw['address']
    #print("Address:",address)
    
    country = address.get('country', '')
    country_code  = address.get('country_code','')
    #print('Country:',country)
    
    country_alpha2 = pc.country_name_to_country_alpha2(country)
    country_continent_code = pc.country_alpha2_to_continent_code(country_alpha2)
    country_continent_name = pc.convert_continent_code_to_continent_name(country_continent_code)
    
    cnn = country_continent_name.lower()
    
    links = CNN_Location_Links(cnn)
    
    for key,item in links.items():
        l = urlopen(item)  
        bsobj = BeautifulSoup(l)
        for head in bsobj.find_all('h1'):
                newhead["Heading" + str(i)]=head.text 
                i+=1
    
    list = {
        "LocationBased":[newhead,links]
    }

    return jsonify(list)

@app.route('/for_you',methods=['GET'])  
def for_you():
    links = For_You_links()
    i = 0
    newhead = {}
    for key,item in links.items():
        l = urlopen(item)  
        bsobj = BeautifulSoup(l)
        for head in bsobj.find('h1'):
                newhead["Heading" + str(i)]= head.text
                i+=1

    list = {
        "IntrestBased":[newhead,links]
    }
    return jsonify(list)
# **************************************************************************************************************
#                    ***************************Functions For TopHndL*****************************
# **************************************************************************************************************

def TopNewsLinks():
    html = urlopen("https://www.bbc.com/news")
    bsObj = BeautifulSoup(html)
    l=0
    i= 0
    j=0
    limit = 10
    newurl={}

    # Finding links
    links = []
    for link in bsObj.find('div', {'id': 'news-top-stories-container'}).find_all('a',href=re.compile("-\d{8}$")):
        if 'href' in link.attrs:
            if link['href'].startswith('https://www.bbc.co.uk/'):
                        continue
            newurl["Url"+str(l)]="https://www.bbc.com"+link.attrs['href']
            l+=1
            if i == limit:
                break
            i+=1



    aj = "https://www.aljazeera.com"
    http = urlopen(aj)
    bsObj = BeautifulSoup(http)
    for anchor in bsObj.find('ul', {'class': 'fte-featured'}).find_all('a'):
        if 'href' in anchor.attrs:
            newurl["Url"+str(l)]="https://www.aljazeera.com"+anchor.attrs['href']
            l+=1
            if j == limit:
                break
            j+=1

    # print(links)
    return (newurl)


# **************************************************************************************************************
#                    ***************************Functions For TrendingHndL*****************************
# **************************************************************************************************************
def TrendingNewsLinks():
    bbc = urlopen("https://www.bbc.com/news")
    bsobj = BeautifulSoup(bbc,'html.parser')
    limit = 8
    l=0
    i = 0
    j =0
    newurl={}
    
    for anchor in bsobj.find('div', {'class': 'nw-c-most-read__items'}).find_all('a'):
        if 'href' in anchor.attrs:
            if anchor['href'].startswith('https://www.bbc.co.uk/'):
                        continue
            newurl["Url"+str(l)]="https://www.bbc.com"+anchor.attrs['href']
            l+=1
            if i == limit:
                break
            i += 1

    aj = urlopen("https://www.aljazeera.com")
    bs = BeautifulSoup(aj,'html.parser')
    for anchor in bs.find('aside', {'id': 'most-read-container'}).find_all('a'):
        if 'href' in anchor.attrs:
            # print(anchor.attrs['href'])
            newurl["Url"+str(l)]="https://www.aljazeera.com"+anchor.attrs['href']
            l+=1
            if j == limit:
                break
            j += 1
    return (newurl)






# **************************************************************************************************************
#                    ***************************Functions For Location Based*****************************
# **************************************************************************************************************
def BBC_Location_Links(cn):
    html = urlopen("https://www.bbc.com/news/world/{}".format(cn))
    bsObj = BeautifulSoup(html)
    newurl = {}
    l=0
    for link in bsObj.find('div',{'id':'index-page'}).find_all('a',href=re.compile("-\d{8}$")):
        if 'href' in link.attrs :
            if link['href'].startswith('https://www.bbc.co.uk/'):
                        continue
            newurl["Url"+str(l)]='https://www.bbc.com'+link.attrs['href']
            l+=1

    for link in bsObj.find_all('li',{'class':'lx-stream__post-container'}):#.find_all('a',href=re.compile("-\d{8}$")):
        if link.find('a',href=re.compile("-\d{8}$")):
            z = link.find('a')
        if 'href' in z.attrs :
            if z['href'].startswith('https://www.bbc.co.uk/'):
                        continue
            newurl["Url"+str(l)]='https://www.bbc.com'+z.attrs['href']
            l+=1
    
    return newurl

def Aljazira_Location_links(cn):
    aj = "https://www.aljazeera.com/{}".format(cn)
    http = urlopen(aj)
    bs = BeautifulSoup(http)
    l=0
    newurl ={}
    for anchor in bs.find('ul',{'class':'featured-articles-list'}).find_all('li'):
        z= anchor.find('a')
        if 'href' in z.attrs:
            if z.attrs['href'].endswith("opinion/") or z.attrs['href'].startswith("https://www.aljazeera.com/program"):
                continue
            newurl["Url"+str(l)]='https://www.aljazeera.com'+z.attrs['href']
            l+=1
    for anchor in bs.find('section',{'id':'news-feed-container'}).find_all('article'):
        z = anchor.find('a')
        if 'href' in z.attrs:
            if z.attrs['href'].endswith("opinion/") or z.attrs['href'].startswith("https://www.aljazeera.com/program/"):
                continue
            newurl["Url"+str(l)]='https://www.aljazeera.com'+z.attrs['href']
            l+=1
    
    return newurl

def CNN_Location_Links(cn):
    html = urlopen("https://edition.cnn.com/world/{}".format(cn))
    bsObj = BeautifulSoup(html)
    l=0
    newurl = {}
    for link in bsObj.find_all('div',{'class':'card'}):
        z = link.find('a')
        if 'href' in z.attrs:
            if z['href'].startswith('/videos/'):
                continue
            newurl["Url"+str(l)]="https://edition.cnn.com"+z.attrs['href']
            l+=1
    
    return newurl

def find_match(url):
    expression = re.compile('\/live-news')
    match = expression.search(url)
    if match:
        return 1
    else :
        return 0

# **************************************************************************************************************
#                    ***************************Functions For Intrest Based*****************************
# **************************************************************************************************************
def Find_For_You_links():
    pr = []
    filename = 'MultinomialNB1.sav'
    model_load = pickle.load(open(filename,'rb'))
    res = model_load.predict(listp)
    pr.append(res)
    pr2 = np.array(pr).tolist()
    res = most_frequent(pr2)
    result = most_frequent(res)
    #print(result)
    if result == '0' or result == '4':
        #health
        html = urlopen("https://www.cbsnews.com/healthwatch/fitness/")
        bsObj = BeautifulSoup(html)
        newurl = {}
        l=0
        for link in bsObj.find('div',{'class':'col-8'}).find_all('a'):
            if 'href' in link.attrs and link['href'].startswith('https://www.cbsnews.com/news') :
                newurl["Url"+str(l)]=link.attrs['href']
                l+=1
        return newurl
    elif result == '2':
        #Entertainemnt
        html = urlopen("https://www.cbsnews.com/entertainment/")
        bsObj = BeautifulSoup(html)
        newurl = {}
        l=0
        for link in bsObj.find('div',{'class':'col-8'}).find_all('a'):
            if 'href' in link.attrs and link['href'].startswith('https://www.cbsnews.com/news') :
                newurl["Url"+str(l)]=link.attrs['href']
                l+=1
        return newurl
    elif result == '1':
        #politics
        html = urlopen("https://www.cbsnews.com/politics/")
        bsObj = BeautifulSoup(html)
        newurl={}
        l=0
        for link in bsObj.find('div',{'class':'col-8'}).find_all('a'):
            if 'href' in link.attrs and link['href'].startswith('https://www.cbsnews.com/news/') :
                newurl["Url"+str(l)]=link.attrs['href']
                l+=1
        return newurl
    elif result == '3':
        #travel
        newurl={}
        l=0
        html = urlopen("https://www.bbc.com/news/science-environment-56837908")
        bsObj = BeautifulSoup(html)
        for link in bsObj.find('div',{'id':'topos-component'}).find_all('a',href=re.compile("-\d{8}$")):
                if 'href' in link.attrs:
                    if link['href'].startswith('https://www.bbc.co.uk/'):
                        continue
                    newurl["Url"+str(l)]='https://www.bbc.com'+link.attrs['href']
                    l+=1
        return newurl
    
    elif result=='6' or result == '5':
        #Food$Drinks
        html = urlopen("https://www.cbsnews.com/healthwatch/diet-and-nutrition/")
        bsObj = BeautifulSoup(html)
        newurl = {}
        l=0
        for link in bsObj.find('div',{'class':'col-8'}).find_all('a'):
            if 'href' in link.attrs and link['href'].startswith('https://www.cbsnews.com/news') :
                newurl["Url"+str(l)]=link.attrs['href']
                l+=1
        return newurl
    elif result == '7':
        #World
        html = urlopen("https://www.cbsnews.com/world/")
        bsObj = BeautifulSoup(html)
        newurl = {}
        l=0
        for link in bsObj.find('div',{'class':'col-8'}).find_all('a'):
            if 'href' in link.attrs and link['href'].startswith('https://www.cbsnews.com/news/') :
                newurl["Url"+str(l)]=link.attrs['href']
                l+=1
        return newurl
    elif result == '8':
        #buisness
        newurl={}
        l=0
        html = urlopen("https://www.bbc.com/news/business")
        bsObj = BeautifulSoup(html)
        for link in bsObj.find('div',{'id':'topos-component'}).find_all('a',href=re.compile("-\d{8}$")):
                if 'href' in link.attrs:
                    if link['href'].startswith('https://www.bbc.co.uk/'):
                        continue
                    newurl["Url"+str(l)]='https://www.bbc.com'+link.attrs['href']
                    l+=1
        return newurl
    elif result == '9':
        #sports
        html = urlopen("https://edition.cnn.com/sport/")
        bsObj = BeautifulSoup(html)
        newurl = {}
        l=0
        for link in bsObj.find_all('div',{'class':'container__field-links'}):
                z = link.find('a')
                if 'href' in z.attrs:
                    if z.attrs['href'].startswith('/videos/'):
                        continue
                    newurl["Url"+str(l)]="https://edition.cnn.com"+z.attrs['href']
                    l+=1
        return newurl
    else :
        html = urlopen("https://www.bbc.com/news")
        bsObj = BeautifulSoup(html)
        newurl = {}
        l=0
        for link in bsObj.find('div', {'id': 'news-top-stories-container'}).find_all('a',href=re.compile("-\d{8}$")):
            if 'href' in link.attrs:
                if link['href'].startswith('https://www.bbc.co.uk/'):
                        continue
                newurl["Url"+str(l)]="https://www.bbc.com"+link.attrs['href']
                l+=1
        return newurl

def For_You_links():
    linkss={}
    i=0
    if len(listp)>0 and len(listp)<30:
        #print('list > 0 and list < 30')
        linkss = Find_For_You_links()
        return linkss
    elif len(listp) == 30 or len(listp) > 30:
        #print('list > 30')
        linkss = Find_For_You_links()
        listp.clear()
        return linkss
    else :
        #print("Else part")
        html = urlopen("https://www.bbc.com/news")
        bsObj = BeautifulSoup(html)
        for link in bsObj.find('div', {'id': 'news-top-stories-container'}).find_all('a',href=re.compile("-\d{8}$")):
            if 'href' in link.attrs:
                if link['href'].startswith('https://www.bbc.co.uk/'):
                        continue
                linkss["Url"+str(i)]="https://www.bbc.com"+link.attrs['href']
                i+=1
        return linkss

def most_frequent(List):
    counter = 0
    num = List[0]
     
    for i in List:
        curr_frequency = List.count(i)
        if(curr_frequency> counter):
            counter = curr_frequency
            num = i
 
    return num

if __name__ == '__main__':
    app.run(port=5000)
#print("Url :", url)
#app.run(port=port_no)

