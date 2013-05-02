#Slapbits 
######_A URL Holding and Annotation platform_
***
####How to use:

For testing purposes, simply run `python slapbits.py` to get your server running at `http://127.0.0.1:5000`

You can access via browser or with Python and Curl as outlined below. Further examples will utilize the Python Requests module.
```Python
from requests import post, get
data = get('http://127.0.0.1:5000')
data.json()
```
```Bash
curl 'http://127.0.0.1:5000' -d "key=your_key_here"
```

######Viewing posts 

_anonymous_ Without a key you can view any posts that are set as `private=False` like:
```Python
data = get('http://127.0.0.1:5000/')
json_data = data.json()
```

######Viewing your posts 

_as a user_ You can supply your key via POST to get access to any posts where your key matches:
```Python
data = post('http://127.0.0.1:5000/', data={'key': 'your_key_here'})
json_data = data.json()
```

######Viewing a single post

You can view a single post by referencing its HASH or ID. If you do not have a matching user key, you will only be able to retrieve `private=False` posts.
```Python
# A public post by id
data = post('http://127.0.0.1:5000/post/', data={'id': 5})
json_data = data.json()

# A public post by hash
data = post('http://127.0.0.1:5000/post/', data={'hash': 'post_hash_here'})
json_data = data.json()

# A private post by id that belongs to your key
data = post('http://127.0.0.1:5000/post/', data={'key': 'your_key_here', 'id': 'post_hash_here'})
json_data = data.json()

# A private post by hash that belongs to your key
data = post('http://127.0.0.1:5000/post/', data={'key': 'your_key_here', 'hash': 'post_hash_here'})
json_data = data.json()
```

######Adding posts

To add a post you must have a valid user key.
```Python
post_dict = {
    'url' = 'http://google.com',
    'note' = 'A place for searching.',
    'key' = 'your_user_key',
    'private' = True}
# Note that private defaults to False so if you do not set to True it is visible to all

result = post('http://127.0.0.1:5000/new/', data=post_dict})

# A successful return will look like this
# {post_id: {post_note, post_privacy_status, post_url}}
result.json()
{u'11': {u'note': u'A place to search.', u'private': True, u'url': u'http://google.com/'}} 
```

######Updating posts

You may update the note or privacy status of any of your posts like:
```Python
post_dict = {
    'key' = 'your_user_key',
    'note' = 'My updated note on this link.',
    'private' = True}
result = post('http://127.0.0.1:5000/post/update/', data=post_dict})
```
