__author__ = 'libochen'


from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.ext import db
import threading
from datetime import datetime
from random import randrange


class Image(db.Model):
    owner_id = db.StringProperty()
    image = db.BlobProperty()
    stream_id = db.StringProperty()
    upload_date = db.DateTimeProperty(auto_now_add=True)
    geo_loc = db.GeoPtProperty()

class Stream(ndb.Model):
    # image_list = ndb.StringProperty(repeated=True)
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
    mylock = threading.Lock()
    count = {}
    # def initialize(self, count):
    #     self.count = count

    @classmethod
    def query_stream(cls, ancestor_key):
        return cls.query(ancestor=ancestor_key).order(-cls.last_add)

    @classmethod
    def insert_with_lock(cls, stream_id, image):
        cls.mylock.acquire()
        print "*******" + str(cls.count) + "*******";
        stream_query = Stream.query(Stream.stream_id == stream_id)
        stream = stream_query.fetch()[0]
        # stream.num_images += 1
        # print "current image numbers: " + str(stream.num_images)
        user_image = Image(parent=db.Key.from_path('Stream', stream_id))
        # stream.image_list.append('0')
        image = images.resize(image, 320, 400)
        user_image.image = db.Blob(image)
        # get random geoPoint
        user_image.geo_loc = db.GeoPt(randrange(-90,90),randrange(-180,180))
        stream.last_add = str(datetime.now())
        user_image.put()
        if stream_id not in cls.count:
            cls.count[stream_id] = 0

        cls.count[stream_id] += 1
        print "entercount numebr is ", cls.count[stream_id]
        stream.num_images = cls.count[stream_id]
        stream.put()
        cls.mylock.release()


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