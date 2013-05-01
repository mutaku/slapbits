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
            backref='user',
            lazy='dynamic')

    def __init__(self, email):
        self.email = email
        self.key = gen_hash(email, length=15)

    def __repr__(self):
        return '<User {0.id} - {0.email}'.format(self)


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

    def __init__(self, url, note, user, private=False):
        self.url = url
        # should we be checking the hash before?
        self.hash = gen_hash(url)
        self.note = note
        self.user = user
        self.private = private

    def long_short(self):
        return self.long_link[:50]

    def __repr__(self):
        return '<Link {0.id} - {0.long_short()}'.format(self)


# Prepare Responses

class Manage(Resource):
    def __init__(self):
        self.args = parser.parse_args()
        if not self.args['hash']:
            abort(404,
                    message="Need a hash.")

    def get(self):
        obj = db.Post.query.filter_by(hash=self.args['hash']).first_or_404()
        if obj.user.key == self.args['key']:
            return jsonify(obj)
        return ' ', 403

    def put(self):
        obj = db.Post.query.get(hash=self.args['hash']).get_or_404()
        if obj.user.key == self.args['key']:
            obj.note = self.args['note']
            obj.note = self.args['private']
            db.session.commit()
            return jsonify(obj), 201
        return ' ', 403

    def delete(self):
        obj = db.Post.query.get(hash=self.args['hash']).get_or_404()
        if obj.user.key == self.args['key']:
            db.session.delete(obj)
            db.session.commit
            return ' ', 204
        return ' ', 403


class ViewAll(Resource):
    def __init__(self):
        self.args = parser.parse_args()

    def get(self):
        # I don't like this approach here
        if self.args.has_key('key'):
            objs = db.User.query.filter_by(key=self.args['key']).get_or_404().posts()
        else:
            objs = db.Post.query.filter_by(private=False).get_or_404()
        return jsonify(objs)

    def post(self):
        user = db.User.query.get(key=self.args['key']).get_or_404()
        post = db.Post(
                url  = self.args['url'],
                note = self.args['note'],
                user = user,
                private = self.args['private'])
        db.session.add(post)
        db.session.commit()
        return jsonify(post), 201

# API resources

parser = reqparse.RequestParser()
parser.add_argument('key', type=str, required=True)
parser.add_argument('hash', type=str)
parser.add_argument('url', type=url)
parser.add_argument('note', type=str)
parser.add_argument('private', type=str)

api.add_resource(ViewAll, '/')
api.add_resource(Manage, '/post/')


if __name__ == '__main__':
    app.run()
