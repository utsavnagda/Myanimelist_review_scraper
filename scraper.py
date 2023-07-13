import requests
from flask import Flask, render_template, request
from bs4 import BeautifulSoup as bs
from pymongo.mongo_client import MongoClient

# connection to mongodb
uri = "mongodb+srv://<username for mongodb>:<password>@cluster0.h4aocj3.mongodb.net/?retryWrites=true&w=majority"

# Create a new client and connect to the server
client = MongoClient(uri)

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

app = Flask(__name__)
@app.route("/", methods = ['GET'])
def homepage():
    return render_template("index.html")

# getting all the results for the search
@app.route("/review" , methods = ['POST' , 'GET'])
def index():
    if request.method == 'POST':
        try:
            search = request.form['content'].replace(" ","")
            url = "https://myanimelist.net/search/all?q=" + f"{search}"
            search_res = bs(requests.get(url=url).text, "html.parser").find_all("div", {"class": "list di-t w100"})
            search_href = []
            for res in search_res:
                try:
                    search_href.append(res.find("div", {"class": "title"}).a["href"])
                except AttributeError:
                    print("Attribute error. Moving on..")
                    break
                except Exception as e:
                    print("Unknown error: ", e)

            # getting review page link from all the search results
            review_page_link = []
            for link in search_href:
                anime_page = bs(requests.get(link).text)
                review_link = "https://myanimelist.net" + anime_page.find("span", {"class": "floatRightHeader"}).a["href"]
                review_page_link.append(review_link)

            # getting all the review details from the page
            rev_dets = []
            for page_link in review_page_link:
                reviews = bs(requests.get(page_link).text).find_all("div", {"class":"review-element js-review-element"})
                
                for review in reviews:
                    body = review.find("div",{"class":"body"})
                    date = body.div.text
                    username = body.find("div", {"class":"username"}).a.text
                    recom = body.find("div", {"class":"tags"}).div.text
                    review = body.find("div", {"class":"text"}).text
                    rating = body.find("div", {"class":"rating mt20 mb20 js-hidden"}).span.text
                    rev = {"date": date, "username": username, "recommendation": recom, "review": review, "rating":rating}
                    rev_dets.append(rev)
            db = client["anime_review_db"]
            collection = db[f"{search}_review_coll"]
            collection.insert_many(rev_dets)
            return render_template('result.html', review_var=rev_dets[0:-1])
        except Exception as e:
            return 'something is wrong'
    else:
        return render_template('index.html')

if __name__=="__main__":
    app.run()
