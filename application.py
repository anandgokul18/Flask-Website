#!flask/bin/python
from flask import Flask, jsonify

from newsapi import NewsApiClient

newsapi = NewsApiClient(api_key='bcd502afe5944e8db5549e521efc93f0')

"""
This function takes in the results from top_headlines and checks the first 'numberofvalidresults' (either 4 or 5) 
results that have all keys (author, description, title, url, urlToImage, publishedAt and source with its inner keys) present.
"""
def top_headlines_resultformatter(top_headlines, numberofvalidresults, detailedResults=False):
    results_dict = {}
    results_dict['articles'] = []

    articles = top_headlines['articles']

    mandatorykeys = ['source', 'author', 'title', 'description', 'url', 'urlToImage', 'publishedAt', 'content']
    sourcekeys = ['id','name']
    for i in range(0,len(articles)):
        if list(articles[i].keys())==mandatorykeys and list(articles[i]['source'].keys())==sourcekeys:
            if (not detailedResults):
                if(articles[i]['title']!=None and articles[i]['description']!=None and articles[i]['url']!=None and articles[i]['urlToImage']!=None and articles[i]['author']!="" and articles[i]['source']!="" and articles[i]['source']['id']!="" and articles[i]['source']['name']!="" ):
                    eacharticle={}
                    eacharticle['title'] = articles[i]['title']
                    eacharticle['description'] = articles[i]['description'].replace("\n"," ")
                    eacharticle['url'] = articles[i]['url']
                    eacharticle['urlToImage'] = articles[i]['urlToImage']
                    if(len(results_dict['articles'])<numberofvalidresults):
                        results_dict['articles'].append(eacharticle)
                    else:
                        return results_dict
            #If detailedResults...For Search Page
            else:
                if(articles[i]['title']!=None and articles[i]['description']!=None and articles[i]['description']!="" and articles[i]['url']!=None and articles[i]['urlToImage']!=None and articles[i]['urlToImage']!="" and articles[i]['author']!=None and articles[i]['publishedAt']!=None and articles[i]['source']['name']!=None ):
                    eacharticle={}
                    eacharticle['title'] = articles[i]['title']
                    eacharticle['description'] = articles[i]['description']
                    eacharticle['url'] = articles[i]['url']
                    eacharticle['author'] = articles[i]['author']
                    eacharticle['source'] = articles[i]['source']['name']

                    #Date to MM-DD-YYYY format from YYYY-MM-DDT...
                    datestr=''
                    resultdate=articles[i]['publishedAt']
                    datestr+=resultdate.split('-')[1]+"/"+resultdate.split('-')[2].split('T')[0]+"/"+resultdate.split('-')[0]
                    eacharticle['date'] = datestr

                    #Short Description
                    listofwords=articles[i]['description'].split(" ")
                    shortdesc=" ".join(listofwords[:12])+'...'
                    eacharticle['shortdesc'] = shortdesc
                    
                    eacharticle['image'] = articles[i]['urlToImage']
                    if(len(results_dict['articles'])<numberofvalidresults):
                        results_dict['articles'].append(eacharticle)
                    else:
                        return results_dict

        else:
            pass


from flask_cors import CORS, cross_origin

application = Flask(__name__)
application.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

cors = CORS(application)
application.config['CORS_HEADERS'] = 'Content-Type'

@application.route('/')
@application.route('/index.html')
@application.route('/index')
@cross_origin()
def root():
    return application.send_static_file('index.html')

@application.route('/news/api/v1.0/homepagearticles', methods=['GET'])
@cross_origin()
def get_homepage_headlines():
    top_headlines = newsapi.get_top_headlines(language='en')
    top_headlines = top_headlines_resultformatter(top_headlines, 5)

    cnn_headlines = newsapi.get_top_headlines(sources='cnn', language='en')
    cnn_headlines = top_headlines_resultformatter(cnn_headlines, 4)

    fox_headlines = newsapi.get_top_headlines(sources='fox-news', language='en')
    fox_headlines = top_headlines_resultformatter(fox_headlines, 4)

    return jsonify({'top_headlines': top_headlines, 'cnn_headlines': cnn_headlines, 'fox_headlines':fox_headlines})


@application.route('/news/api/v1.0/wordcloud', methods=['GET'])
@cross_origin()
def get_wordcloud_words():
    top_headlines = newsapi.get_top_headlines(language='en')
    query = ''
    articles = top_headlines['articles']
    for i in range(0,len(articles)):
        query+=articles[i]['title'].lower()+" "

    #Removing stop words
    stopwordsfile = open('stopwords_en.txt', 'r')
    stopwords = [line.split('\n')[0] for line in stopwordsfile.readlines()]

    querywords = query.split()
    resultwords  = [word for word in querywords if word.lower() not in stopwords]
    result = ' '.join(resultwords)


    from collections import Counter 
    split_it = result.split() 
    Counter = Counter(split_it) 
    most_occur = Counter.most_common(30) #Get 30 most frequent words

    most_frequent_results=[]
    for i in range(0,len(most_occur)):
        mydict={}
        mydict['size'] = str(most_occur[i][1])
        mydict['word'] = str(most_occur[i][0])
        most_frequent_results.append(mydict)


    return jsonify({'most_frequent_results': most_frequent_results})

@application.route('/news/api/v1.0/sourcelist', methods=['GET'])
@cross_origin()
def get_sources():
    sources = newsapi.get_sources()
    sources = sources['sources']

    return jsonify({'sources': sources})


from flask import request
@application.route("/search/", methods=['GET'])
@cross_origin()
def do_search():
    keyword = request.args['keyword']
    fromdate = request.args['fromdate']
    todate = request.args['todate']
    category = request.args['category']
    sources = request.args['sources']

    try:
        if sources=='all':
            searchresults = newsapi.get_everything(q=keyword, from_param=fromdate, to=todate, language='en', sort_by='publishedAt', page=1, page_size=30)
        else:
            searchresults = newsapi.get_everything(q=keyword, sources=sources, from_param=fromdate, to=todate, language='en', sort_by='publishedAt', page=1, page_size=30)        

        searchresults = top_headlines_resultformatter(searchresults, 15, detailedResults=True)

    except Exception as e:
        errormessage = str(e)
        import yaml
        dictofmessage = yaml.load(errormessage)
        searchresults={'errormessage': dictofmessage['message']}


    searchquery = {'keyword': keyword, 'fromdate': fromdate, 'todate': todate, 'category': category, 'sources':sources}

    return jsonify({'searchresults': searchresults, 'searchquery': searchquery})


"""
@application.route("/search/?keyword=<keyword>&fromdate=<fromdate>&todate=<todate>&category=<category>&sources=<sources>", methods=['GET'])
def do_search(keyword,fromdate,todate,category,sources):
    print("--------------YEET!-----------------")
    if sources=='all':
        searchresults = newsapi.get_everything(q=keyword, from_param=fromdate, to=todate, language='en', sortBy='publishedAt', pageSize=30, page=1)
    else:
        searchresults = newsapi.get_everything(q=keyword, sources=sources, from_param=fromdate, to=todate, language='en', sortBy='publishedAt', pageSize=30, page=1)        

    return jsonify({'searchresults': searchresults})


@application.route('/news/api/v1.0/cnn', methods=['GET'])
def get_tasks():
    return jsonify({'tasks': [make_public_task(task) for task in tasks]})


@application.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = [task for task in tasks if task['id'] == task_id]
    if len(task) == 0:
        abort(404)
    return jsonify({'task': task[0]})

from flask import make_response

@application.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

from flask import url_for

def make_public_task(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task
"""

if __name__ == '__main__':
    application.run(debug=True)