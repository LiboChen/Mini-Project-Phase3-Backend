__author__ = 'libochen'


from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.ext import db


class Image(db.Model):
    owner_id = db.StringProperty()
    image = db.BlobProperty()
    stream_id = db.StringProperty()
    upload_date = db.DateTimeProperty(auto_now_add=True)


class Stream(ndb.Model):
    owner = ndb.StringProperty()       #used to solve can't see others problem
    stream_id = ndb.StringProperty()
    user_id = ndb.StringProperty()
    last_add = ndb.StringProperty()
    views = ndb.IntegerProperty()
    num_images = ndb.IntegerProperty()
    cover_url = ndb.StringProperty()
    subscribers = ndb.StringProperty(repeated=True)
    tags = ndb.StringProperty()
    view_queue = ndb.DateTimeProperty(repeated=True)

    @classmethod
    def query_stream(cls, ancestor_key):
        return cls.query(ancestor=ancestor_key).order(-cls.last_add)




class StreamInfo(ndb.Model):
    created = ndb.KeyProperty(repeated=True)
    subscribed = ndb.KeyProperty(repeated=True)

    @classmethod
    def query_stream(cls, ancestor_key):
        return cls.query(ancestor=ancestor_key)


class ShowStream:
    def __init__(self, image_url, views, stream_id):
        self.url = image_url
        self.views = views
        self.stream_id = stream_id




'''
class User(ndb.Model):
    user_id = ndb.StringProperty()
    upload_streams = ndb.StringProperty(repeated=True)
    subscribe_streams = ndb.StringProperty(repeated=True)

    def add_stream(self, new_stream):
        if new_stream.stream_id in self.upload_streams:
            return
        else:
            self.upload_streams.insert(0, new_stream.stream_id)

        self.put()
        new_stream.put()
'''