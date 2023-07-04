## What is this?

This is my own application for posting Twitter-like tweets.
Tweets are stored in MongoDB.

* Python + Flask
* MongoDB


### Features to be supported in the near future

* Real-time tweet acquisition (use Change Streams for MongoDB)
* infinity scroll
* Markdown support for tweets

## How to Develop

```
% docker compose up -d
% docker exec -it admonish-grumbler-app /bin/bash
# pip install --upgrade pip
# pip install -r requirements.txt
# python run.py
```

Access to http://localhost:5500 from your browser.
