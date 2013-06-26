#Slapbits 
######_A URL Holding and Annotation platform_
Slapbits provides a RESTful API for saving and annotating URLs using the Flask framework.

***
####How to use:


######Running the test server
For testing purposes, simply run `python slapbits.py` to get your server running at `http://127.0.0.1:5000` or configure:
```Shell
python slapbits.py {-d -h host_ip_address -p port_number}

-d -> debug mode
-h host_ip_address -> server IP address (defaults to 127.0.0.1 for localhost only connections)
-p port_number -> server port (defaults to 5000)
```

######Populating users
```Python
import slapbits

new_user = slapbits.User(email="your_email_address")
slapbits.db.session.add(new_user)
slapbits.db.session.commit()

#Your access key
my_new_api_key = new_user.key
```

######Basic access methods

You can access via browser or with Python and Curl as outlined below. Further examples will utilize the Python Requests module.
```Python
from requests import post, get
data = get('http://127.0.0.1:5000')
data.json()
```
```Bash
curl 'http://127.0.0.1:5000/api/' -d "key=your_key_here"
```

######Viewing posts 

_anonymous_ Without a key you can view any posts that are set as `private=False` like:
```Python
data = get('http://127.0.0.1:5000/api/')
json_data = data.json()
```

######Viewing your posts 

_as a user_ You can supply your key via POST to get access to any posts where your key matches:
```Python
data = post('http://127.0.0.1:5000/api/', data={'key': 'your_key_here'})
json_data = data.json()
```

######Viewing a single post

You can view a single post by referencing its HASH or ID. If you do not have a matching user key, you will only be able to retrieve `private=False` posts.
```Python
# A public post by id
data = post('http://127.0.0.1:5000/api/post/', data={'id': 5})
json_data = data.json()

# A public post by hash
data = post('http://127.0.0.1:5000/api/post/', data={'hash': 'post_hash_here'})
json_data = data.json()

# A private post by id that belongs to your key
data = post('http://127.0.0.1:5000/api/post/', data={'key': 'your_key_here', 'id': 'post_hash_here'})
json_data = data.json()

# A private post by hash that belongs to your key
data = post('http://127.0.0.1:5000/api/post/', data={'key': 'your_key_here', 'hash': 'post_hash_here'})
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

result = post('http://127.0.0.1:5000/api/new/', data=post_dict})

# A successful return will look like this
# {post_id: {post_note, post_privacy_status, post_url}}
result.json()
{u'11': {u'note': u'A place to search.', u'private': True, u'url': u'http://google.com/'}} 
```

######Updating posts

You may update the note or privacy status of any of your posts using _either_ hash or id like:
```Python
# with HASH
post_dict = {
    'key' = 'your_user_key',
    'hash' = 'post_hash_to_update',
    'note' = 'My updated note on this link.',
    'private' = True}
result = post('http://127.0.0.1:5000/api/post/update/', data=post_dict})

# or with ID
post_dict = {
    'key' = 'your_user_key',
    'id' = 'post_id_to_update',
    'note' = 'My updated note on this link.',
    'private' = True}
result = post('http://127.0.0.1:5000/api/post/update/', data=post_dict})
```
