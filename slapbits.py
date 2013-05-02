# -*- coding: utf-8 -*-
#########################################
# Slapbits
#   A URL Holding and Annotation platform
#   Matthew Martz 2013
#   License: BSD
#########################################

from flask import Flask, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restful import reqparse, abort, Api, Resource
from hashlib import sha224
from local_settings import HASH_KEY

app = Flask(__name__)
app.config.from_object('local_settings')

api = Api(app)
db = SQLAlchemy(app)


# Models

def gen_hash(data, length=56):
    return sha224(data+HASH_KEY).hexdigest()[:length]


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
        self.hash = gen_hash(url)
        self.url = url
        self.note = note
        self.author = author
        self.private = private


    def __repr__(self):
        return '<Link {0.id} - {0.hash}>'.format(self)


def build_query_dictionary(obj):
        data = dict()
        data['url'] = obj.url
        data['note'] = obj.note
        data['private'] = obj.private
        return data

def queryset_to_json(queryset):
    # this needs some work
    result = dict()
    if type(queryset) is list:
        for obj in queryset:
            result[obj.id] = build_query_dictionary(obj)
    else:
        result[queryset.id] = build_query_dictionary(queryset)
    return jsonify(result)


# Prepare Responses

class View(Resource):
    def __init__(self):
        self.args = parser.parse_args()
        if not self.args['hash']:
            abort(404,
                    message="Need a hash.")
        # try to ID user or 404
        User.query.filter_by(key=self.args['key']).first_or_404()

    def post(self):
        obj = Post.query.filter_by(hash=self.args['hash']).first_or_404()
        if obj.author.key == self.args['key']:
            return queryset_to_json(obj)
        return ' ', 403

class Update(Resource):
    def __init__(self):
        self.args = parser.parse_args()
        if not self.args['hash']:
            abort(404,
                    message="Need a hash.")
        # try to ID user or 404
        User.query.filter_by(key=self.args['key']).first_or_404()

    def post(self):
        obj = Post.query.filter_by(hash=self.args['hash']).first()
        if obj.author.key == self.args['key']:
            obj.note = self.args['note']
            obj.private = self.args['private']
            db.session.commit()
            post_object = Post.query.get(obj.id)
            return queryset_to_json(post_object)
        return ' ', 403

class Delete(Resource):
    def __init__(self):
        self.args = parser.parse_args()
        if not self.args['hash']:
            abort(404,
                    message="Need a hash.")
        # try to ID user or 404
        User.query.filter_by(key=self.args['key']).first_or_404()

    def post(self):
        obj = Post.query.filter_by(hash=self.args['hash']).first_or_404()
        if obj.author.key == self.args['key']:
            db.session.delete(obj)
            db.session.commit
            # Doesn't seem to be deleting
            return 'Deleted'
        return ' ', 403


class ViewAll(Resource):
    def post(self):
        self.args = parser.parse_args()
        # try to ID user or 404
        User.query.filter_by(key=self.args['key']).first()
        objs = Post.query.join(User).filter(User.key==self.args['key']).all()
        return queryset_to_json(objs)

    def get(self):
        objs = Post.query.filter_by(private=False).all()
        return queryset_to_json(objs)


class New(Resource):
    def __init__(self):
        self.args = parser.parse_args()
        # try to ID user or 404
        self.user = User.query.filter_by(key=self.args['key']).first_or_404()

    def post(self):
        post = Post(
                url  = self.args['url'],
                note = self.args['note'],
                author = self.user,
                private = self.args['private'])
        db.session.add(post)
        db.session.commit()
        post_object = Post.query.get(post.id)
        return queryset_to_json(post_object)

# API resources
from flask.ext.restful import types
parser = reqparse.RequestParser()
parser.add_argument('key', type=str)
parser.add_argument('hash', type=str)
parser.add_argument('url', type=str)
parser.add_argument('note', type=str)
parser.add_argument('private', type=types.boolean)

api.add_resource(ViewAll, '/')
api.add_resource(New, '/new/')
api.add_resource(View, '/post/')
api.add_resource(Update, '/post/update/')
api.add_resource(Delete, '/post/delete/')


if __name__ == '__main__':
    app.run(debug=True)
