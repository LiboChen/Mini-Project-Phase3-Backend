__author__ = 'libochen'


from google.appengine.ext import ndb
from google.appengine.ext import blobstore


class Image(ndb.Model):
    owner_id = ndb.StringProperty()
    blob_key = ndb.BlobKeyProperty()
    stream_id = ndb.StringProperty()


class Stream(ndb.Model):
    owner = ndb.StringProperty()       #used to solve can't see others problem
    stream_id = ndb.StringProperty()
    user_id = ndb.StringProperty()
    last_add = ndb.StringProperty()
    views = ndb.IntegerProperty()
    num_images = ndb.IntegerProperty()
    cover_url = ndb.StringProperty()
    subscribers = ndb.StringProperty(repeated=True)
    tags = ndb.StringProperty(repeated=True)
    blob_key = ndb.BlobKeyProperty(repeated=True)

    @classmethod
    def query_stream(cls, ancestor_key):
        return cls.query(ancestor=ancestor_key).order(-cls.last_add)


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