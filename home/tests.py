import tweepy 

api_key = "ELzMQYCnkWNopu8WfwQV0ggIu"
api_secret = "yAtL6T1Qi94O15sx1kJUmx3T0F3msMISwdfNUgfWVd1Nn5bBDY"
bearer_token = "AAAAAAAAAAAAAAAAAAAAAKjbvgEAAAAAU6cN0qrHRDljJGFRJJB6Kg6vmPE%3DQtfOs3JXLSCleBmc7LB0HWS0DhYlq8CMbRj6fnrCzRpcFSH9L4"
access_token = "1709186859757101056-OOuCwUcD1HqnJz7iqvHZ4KwryGdW1d"
access_token_secret = "pTIdyP1SAY3KV7OB3QV0WQHpfdx6aNHqACAZ27MRBC0d4"

# client = tweepy.Client(bearer_token, api_key, api_secret, access_token,access_token_secret)


auth = tweepy.OAuthHandler(api_key, api_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

query = 'python'
num_tweets = 100

tweets = tweepy.Cursor(api.search_tweets, q=query).items(num_tweets)

for tweet in tweets:
    print(tweet.media)