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


# Prepare Responses

class Manage(Resource):
    def __init__(self):
        self.args = parser.parse_args()
        if not self.args['hash']:
            abort(404,
                    message="Need a hash.")
        # try to ID user or 404
        db.User.query.filter_by(key=self.args['key']).get_or_404()

    def get(self):
        obj = db.Post.query.filter_by(hash=self.args['hash']).get_or_404()
        if obj.user.key == self.args['key']:
            return jsonify(obj)
        return ' ', 403

    def put(self):
        obj = db.Post.query.filter_by(hash=self.args['hash']).get_or_404()
        if obj.user.key == self.args['key']:
            obj.note = self.args['note']
            obj.note = self.args['private']
            db.session.commit()
            return jsonify(obj), 201
        return ' ', 403

    def delete(self):
        obj = db.Post.query.filter_by(hash=self.args['hash']).get_or_404()
        if obj.user.key == self.args['key']:
            db.session.delete(obj)
            db.session.commit
            return ' ', 204
        return ' ', 403


class View(Resource):
    def __init__(self):
        self.args = parser.parse_args()
        # try to ID user or 404
        db.User.query.filter_by(key=self.args['key']).get_or_404()

    def get(self):
        # I don't like this approach here
        if self.args.has_key('key'):
            objs = db.Post.query.join(User).filter(User.key==self.args['key'])
        else:
            objs = db.Post.query.filter_by(private=False).all()
        return jsonify(objs)

    def post(self):
        user = db.User.query.filter_by(key=self.args['key']).get_or_404()
        post = db.Post(
                url  = self.args['url'],
                note = self.args['note'],
                author = user,
                private = self.args['private'])
        db.session.add(post)
        db.session.commit()
        return jsonify(post), 201

# API resources

parser = reqparse.RequestParser()
parser.add_argument('key', type='str', required=True)
parser.add_argument('hash', type='str')
parser.add_argument('url', type='url')
parser.add_argument('note', type='str')
parser.add_argument('private', type='str')

api.add_resource(View, '/')
api.add_resource(Manage, '/post/')


if __name__ == '__main__':
    app.run()
