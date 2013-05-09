# -*- coding: utf-8 -*-
#########################################
# Slapbits
#   A URL Holding and Annotation platform
#   Matthew Martz 2013
#   License: BSD
#########################################

from flask import Flask
from flask import jsonify as _jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restful import types, reqparse, abort, Api, Resource
from hashlib import sha224
from local_settings import HASH_KEY
import sys
import getopt
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)
app.config.from_object('local_settings')

api = Api(app)

db = SQLAlchemy(app)


# Models

class User(db.Model):
    id = db.Column(db.Integer,
            primary_key=True)
    email = db.Column(db.String(255),
            unique=True)
    key = db.Column(db.String(15),
            unique=True)
    posts = db.relationship('Post',
            backref='author',
            lazy='dynamic')

    def __init__(self, email):
        self.key = gen_hash(email, length=15)
        self.email = email

    def __repr__(self):
        return '<User {0.email}>'.format(self)


class Post(db.Model):
    id = db.Column(db.Integer,
            primary_key=True)
    hash = db.Column(db.String(56),
            unique=True)
    url = db.Column(db.Text)
    note = db.Column(db.Text)
    user = db.Column(db.Integer,
            db.ForeignKey('user.id'))
    private = db.Column(db.Boolean,
            default=False)

    def __init__(self, url, note, author, private=False):
        self.url = url
        self.note = note
        self.author = author
        self.private = private
        self.hash = gen_hash(url+self.author.key)

    def __repr__(self):
        return '<Link {0.id} - {0.hash}>'.format(self)


# Utilities

def gen_hash(data, length=56):
    return sha224(data+HASH_KEY).hexdigest()[:length]

def build_query_dictionary(obj):
        data = obj.__dict__.copy()
        data.pop('_sa_instance_state', None)
        data.pop('user', None)
        data.pop('author', None)
        data.pop('id', None) # we use this as result key
        # SHOULD WE TAKE OUT HASH?
        return data

def queryset_to_json(status_code, queryset):
    # this needs some work
    result = dict()
    if isinstance(queryset, list):
        for obj in queryset:
            result[obj.id] = build_query_dictionary(obj)
    else:
        result[queryset.id] = build_query_dictionary(queryset)
    return jsonify(status_code, result)

def jsonify(status_code, *args, **kwargs):
    response = _jsonify(*args, **kwargs)
    if status_code:
        response.status_code = status_code
    return response


# Prepare Responses

class ViewPost(Resource):
    def __init__(self):
        self.args = parser.parse_args()
        if not self.args['hash'] and not self.args['id']:
            abort(404,
                    message="Need a hash or id.")

    def post(self):
        if self.args['id']:
            obj = Post.query.get_or_404(self.args['id'])
        else:
            obj = Post.query.filter_by(hash=self.args['hash']).first_or_404()
        if (self.args['key'] and obj.author.key == self.args['key']
                or not obj.private):
            return queryset_to_json(200, obj)
        return ' ', 403


class UpdatePost(Resource):
    def __init__(self):
        self.args = parser.parse_args()
        if not self.args['hash'] and not self.args['id']:
            abort(404,
                    message="Need a hash or id.")
        # try to ID user or 404 - not needed but saves us from proceeding
        User.query.filter_by(key=self.args['key']).first_or_404()

    def post(self):
        # this needs improved
        if self.args['hash']:
            obj = Post.query.join(User).filter(
                    (User.key == self.args['key']) &
                    (Post.hash == self.args['hash'])).first()
        else:
            obj = Post.query.join(User).filter(
                    (User.key == self.args['key']) &
                    (Post.id == self.args['id'])).first()
        if obj:
            if self.args['note']:
                obj.note = self.args['note']
            obj.private = self.args['private']
            db.session.commit()
            post_object = Post.query.get(obj.id)
            return queryset_to_json(201, post_object)
        return ' ', 403


class ViewAll(Resource):
    def post(self):
        self.args = parser.parse_args()
        objs = Post.query.join(User).filter_by(key=self.args['key']).all()
        return queryset_to_json(200, objs)

    def get(self):
        objs = Post.query.filter_by(private=False).all()
        return queryset_to_json(200, objs)


class AddPost(Resource):
    def post(self):
        self.args = parser.parse_args()
        self.user = User.query.filter_by(key=self.args['key']).first_or_404()
        post = Post(
                url  = self.args['url'],
                note = self.args['note'],
                author = self.user,
                private = self.args['private'])
        db.session.add(post)
        try:
            db.session.commit()
            post_object = Post.query.get(post.id)
            return queryset_to_json(201, post_object)
        except IntegrityError, error:
            return jsonify(418, Error=error.message)


# API resources

arguments = (
    ('key', str),
    ('hash', str),
    ('url', types.url),
    ('note', str),
    ('private', types.boolean),
    ('id', int)
    )

parser = reqparse.RequestParser()
for arg, arg_type in arguments:
    parser.add_argument(arg, type=arg_type)

views = (
    (ViewAll, '/api/'),
    (AddPost, '/api/new/'),
    (ViewPost, '/api/post/'),
    (UpdatePost, '/api/post/update/')
    )

for view_method, endpoint in views:
    api.add_resource(view_method, endpoint)


# Instantiation with built-in server

if __name__ == '__main__':
    vars = dict(debug=False)
    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(args, 'dh:p:')
    except getopt.GetoptError:
        sys.exit(2)

    for opt, arg in opts:
        # Enable debugging
        if opt == '-d':
            vars['debug'] = True
        if opt == '-h':
            vars['host'] = arg
        if opt == '-p':
            vars['port'] = int(arg)

    print "Running with {}".format(vars)
    app.run(**vars)
