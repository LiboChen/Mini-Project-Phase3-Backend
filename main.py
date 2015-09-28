#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import webapp2
import json
import urllib
from data_class import Stream, StreamInfo, ShowStream
from datetime import datetime
from google.appengine.api import users
from google.appengine.api import images
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
import jinja2
from collections import OrderedDict



JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader('templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


NAV_LINKS = sorted(('Create', 'View', 'Search', 'Trending', 'Manage'))
NAV_LINKS = OrderedDict(zip(NAV_LINKS, map(lambda x: '/'+x.lower(), NAV_LINKS) ))
USER_NAV_LINKS = NAV_LINKS.copy()


class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            print 'i am here'
            url = users.create_login_url('/manage')
            url_linktext = 'Login'

        template_values = {
            'user': user,
            'nav_links': USER_NAV_LINKS,
            'path': os.path.basename(self.request.path).capitalize(),
            'user_id': self.request.get('user_id'),
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class LoginHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.response.headers['Content-Type'] = 'text/html; charset=utf-8'
            self.response.write('Hello, ' + user.nickname())
        else:
            self.redirect(users.create_login_url(self.request.uri))
        self.redirect('/manage')


class ManageHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        print 'user is ', user
        subscribed_streams = []
        qry = StreamInfo.query_stream(ndb.Key('User', str(user))).fetch()
        if len(qry) > 0:
            for key in qry[0].subscribed:
                subscribed_streams.append(key.get())

        print subscribed_streams
        template_values = {
            'nav_links': USER_NAV_LINKS,
            'path': os.path.basename(self.request.path).capitalize(),
            'user_id': users.get_current_user(),
            'user_streams': Stream.query(Stream.owner == str(user)).fetch(),
            'subscribed_streams': subscribed_streams,
            'usr': user,
        }

        # all_streams = Stream.query(Stream.stream_id != '').fetch()
        # for s in all_streams:
        #     print s.stream_id
        #
        # print 'length of user_stream', len(template_values['user_streams'])
        # print 'length of subscribed streams', len(template_values['subscribed_streams'])

        template = JINJA_ENVIRONMENT.get_template('manage.html')
        self.response.write(template.render(template_values))
        print "in manage page, "

    def post(self):
        form = {'stream_id': self.request.get_all('stream_id'),
                'user': str(users.get_current_user()),
                }


        form_data = json.dumps(form)
        if self.request.get('delete'):
            result = urlfetch.fetch(payload=form_data, url='http://localhost:8080/delete_a_stream',
                               method=urlfetch.POST, headers={'Content-Type': 'application/json'})
            # result = urlfetch.fetch(payload=form_data, url='http://localhost:8080/delete_a_stream',
            #                         method=urlfetch.POST, headers={'Content-Type': 'application/json'})
        if self.request.get('unsubscribe'):
            result = urlfetch.fetch(payload=form_data, url='http://localhost:8080/unsubscribe_a_stream',
                               method=urlfetch.POST, headers={'Content-Type': 'application/json'})
            # result = urlfetch.fetch(payload=form_data, url='http://localhost:8080/unsubscribe_a_stream',
            #                         method=urlfetch.POST, headers={'Content-Type': 'application/json'})

        self.redirect('/manage')


class CreateHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {
            'nav_links': USER_NAV_LINKS,
            'path': os.path.basename(self.request.path).capitalize(),
            'user_id': self.request.get('user_id'),
        }

        print template_values['user_id']
        template = JINJA_ENVIRONMENT.get_template('create.html')
        self.response.write(template.render(template_values))

    def post(self):
        user = users.get_current_user()
        if self.request.get("subscribers"):
            mail.send_mail(sender=str(user)+"<"+str(user)+"@gmail.com>",
                           to="<"+self.request.get("subscribers")+">",
                           subject="Please subscribe my stream",
                           body=self.request.get("message"))

        self.request
        form = {'stream_id': self.request.get('stream_id'),
                'user_id': str(users.get_current_user()),
                'tags': self.request.get('tags'),
#               'subscribers': self.request.get('subscribers'),
                'cover_url': self.request.get('cover_url'),
                'owner': str(users.get_current_user()),
                'views': 0,
                }

        form_data = json.dumps(form)
        result = urlfetch.fetch(payload=form_data, url='http://localhost:8080/create_a_new_stream',
                                method=urlfetch.POST, headers={'Content-Type': 'application/json'})
        # result = urlfetch.fetch(payload=form_data, url='http://localhost:8080/create_a_new_stream',
        #                         method=urlfetch.POST, headers={'Content-Type': 'application/json'})
        self.redirect('/manage')


class ViewSingleHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        stream_id = self.request.get('stream_id')
        print 'stream id is', stream_id
        info = {'stream_id': self.request.get('stream_id')}
        info = urllib.urlencode(info)
        upload_url = blobstore.create_upload_url('/upload_image?'+info)

#       we should use the actual user
        user_streams = Stream.query(Stream.stream_id == stream_id).fetch()
        blob_key_list = []
        image_url = [""] * 3

        # for stream in user_streams:
        #     owner = stream.owner
        #     print 'stream id is', stream.stream_id
        #     if stream.stream_id == stream_id:
        #         blob_key_list = stream.blob_key

        stream = user_streams[0]
        owner = stream.owner
        print 'stream id is', stream.stream_id
        if owner != str(user):
            stream.views += 1
            stream.view_queue.append(datetime.now())
            stream.put()
        blob_key_list = stream.blob_key     #get blob_key_list should be after stream.put()

        counter = 0
        has_image = True
        if len(blob_key_list) > 0:
            for blob_key in blob_key_list:
                image_url[counter] = images.get_serving_url(blob_key)
                counter += 1
                if counter == 3:
                    break;

        #calculate hasSub
        qry = StreamInfo.query_stream(ndb.Key('User', str(user))).fetch()
        has_sub = False
        if len(qry) == 0:
            has_sub = False
        else:
            for key in qry[0].subscribed:
                if key.get().stream_id == stream_id:
                    has_sub = True
                    break

        template_values = {
            'nav_links': USER_NAV_LINKS,
            'path': os.path.basename(self.request.path).capitalize(),
            'owner': owner,         #the owner of the stream
            'user': str(users.get_current_user()),   #current user
            'upload_url': upload_url,
            'image_url': image_url,
            'has_image': has_image,
            'hasSub': has_sub,
            'stream_id': stream_id,
        }

        print "owner is ", template_values['owner']
        print "user is ", template_values['user']
        template = JINJA_ENVIRONMENT.get_template('viewstream.html')
        self.response.write(template.render(template_values))

    def post(self):
        form = {'stream_id': str(self.request.get('stream_id')),
                'user': str(users.get_current_user()),
                }
        form_data = json.dumps(form)
        if self.request.get('Subscribe') == 'Subscribe':
          result = urlfetch.fetch(payload=form_data, url='http://localhost:8080/subscribe_a_stream',
                               method=urlfetch.POST, headers={'Content-Type': 'application/json'})
          #   result = urlfetch.fetch(payload=form_data, url='http://localhost:8080/subscribe_a_stream',
          #                           method=urlfetch.POST, headers={'Content-Type': 'application/json'})
        elif self.request.get('Subscribe') == 'Unsubscribe':
            result = urlfetch.fetch(payload=form_data, url='http://localhost:8080/unsubscribe_a_stream',
                                    method=urlfetch.POST, headers={'Content-Type': 'application/json'})
            # result = urlfetch.fetch(payload=form_data, url='http://localhost:8080/unsubscribe_a_stream',
            #                         method=urlfetch.POST, headers={'Content-Type': 'application/json'})
        self.redirect('/manage')


class ViewAllHandler(webapp2.RequestHandler):
    def get(self):
        streams = Stream.query(Stream.stream_id != '').fetch()
        print type(streams)
        image_url = []
        for stream in streams:
            if stream.cover_url:
                image_url.append([stream.cover_url, stream.stream_id])
            else:
                blob_key_list = stream.blob_key
                if len(blob_key_list) > 0:
                    blob_key = blob_key_list[0]
                    image_url.append([images.get_serving_url(blob_key), stream.stream_id])

        template_values = {
            'nav_links': USER_NAV_LINKS,
            'path': os.path.basename(self.request.path).capitalize(),
            'user': self.request.get('user'),
            'image_url': image_url,
        }

        template = JINJA_ENVIRONMENT.get_template('viewall.html')
        self.response.write(template.render(template_values))


class SearchHandler(webapp2.RequestHandler):
    def get(self):
        pattern = self.request.get("qry")
        print pattern
        all_streams = Stream.query(Stream.stream_id != '').fetch()
        search_result = []
        if pattern:
            for stream in all_streams:
                if pattern in stream.stream_id:
                    stream_id = stream.stream_id
                    blob_key_list = stream.blob_key
                    if stream.cover_url != '':
                        image_url = stream.cover_url
                    elif len(blob_key_list) == 0:
                        image_url = ''
                    else:
                        image_url = images.get_serving_url(blob_key_list[0])
                    result = ShowStream(image_url, 0, stream_id)
                    search_result.append(result)

        template_values = {
            'nav_links': USER_NAV_LINKS,
            'path': os.path.basename(self.request.path).capitalize(),
            'user_id': self.request.get('user_id'),
            'query_results': search_result,
        }

        template = JINJA_ENVIRONMENT.get_template('search.html')
        self.response.write(template.render(template_values))

    def post(self):
        print "seraching "
        info = {'qry': self.request.get('query')}
        self.redirect('/search?'+urllib.urlencode(info))


class TrendingHandler(webapp2.RequestHandler):
    def get(self):
        first_three = []
        all_streams = Stream.query(Stream.stream_id != '').fetch()
        mycmp = lambda x, y: (len(y.view_queue) - len(x.view_queue))
        all_streams.sort(mycmp)
        size = 3 if (len(all_streams) - 3) > 0 else len(all_streams)
        print size
        for i in range(size):
            stream = all_streams[i]
            #print "current stream is", stream
            views = len(stream.view_queue)
            stream_id = stream.stream_id
            blob_key_list = stream.blob_key
            if stream.cover_url != '':
                image_url = stream.cover_url
            elif len(blob_key_list) == 0:
                image_url = ''
            else:
                image_url = images.get_serving_url(blob_key_list[0])

            trending_stream = ShowStream(image_url, views, stream_id)

            print "current trending stream is", trending_stream
            first_three.append(trending_stream)
            print trending_stream.url
        print "end for loop"

        template_values = {
            'nav_links': USER_NAV_LINKS,
            'path': os.path.basename(self.request.path).capitalize(),
            'user_id': self.request.get('user_id'),
            'streams': first_three,
        }

        template = JINJA_ENVIRONMENT.get_template('trending.html')
        self.response.write(template.render(template_values))

    def post(self):
        print "hellp"

class ErrorHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {
            'nav_links': USER_NAV_LINKS,
            'path': os.path.basename(self.request.path).capitalize(),
            'user_id': self.request.get('user_id'),
            'error': 'create duplicate image',
        }

        template = JINJA_ENVIRONMENT.get_template('error.html')
        self.response.write(template.render(template_values))


#############################################################################################
class CreateANewStreamHandler(webapp2.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        user = data['user_id']
        print user, ' is creating'
        new_stream = Stream(parent=ndb.Key('User', user),
                            stream_id=data['stream_id'],
                            user_id=data['user_id'],
                            tags=data['tags'],
                            cover_url=data['cover_url'] if 'cover_url' in data else '',
                            views=0,
                            num_images=0,
                            last_add=str(datetime.now()),
                            owner=data['owner']
                            )

        new_stream.put()
        result = json.dumps({'status': '0'})
        self.response.write(result)


class DeleteStreamHandler(webapp2.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        user = data['user']
        for stream_id in data['stream_id']:
            qry = Stream.query(Stream.stream_id == stream_id).fetch()
            if len(qry) > 0:
                qry[0].key.delete()
            self.redirect('/manage')


class SubscribeStreamHandler(webapp2.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        user = data['user']
        stream_id = data['stream_id']
        print stream_id, 'hello'
        qry = Stream.query(Stream.stream_id == stream_id).fetch()
        print 'lenght of qry is ', len(qry)

        ancestor_key = ndb.Key('User', user)
        stream_info = StreamInfo.query_stream(ancestor_key).fetch()
        if len(stream_info) == 0:
            print 'create a new stream_info'
            new_stream_info = StreamInfo(parent=ndb.Key('User', user))
            new_stream_info.subscribed.insert(0, qry[0].key)
            new_stream_info.put()
        else:
            new_stream_info = stream_info[0]
            new_stream_info.subscribed.insert(0, qry[0].key)
            new_stream_info.put()

        print 'finished'
        self.redirect('/manage')


class UnsubscribeStreamHandler(webapp2.RequestHandler):
    def post(self):
        print 'in unsubscribe handler'
        data = json.loads(self.request.body)
        user = data['user']
        stream_id = data['stream_id']
        print user, 'doing', stream_id
        ancestor_key = ndb.Key('User', user)
        stream_info = StreamInfo.query_stream(ancestor_key).fetch()
        print stream_info[0].subscribed
        for key in stream_info[0].subscribed:
            print key.get().stream_id, stream_id
            if key.get().stream_id == stream_id:
                stream_info[0].subscribed.remove(key)
                stream_info[0].put()       #remember to put it back in ndbstore
                break

        self.redirect('/manage')


class UploadImageHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        print 'stream id is', self.request.get('stream_id')
        try:
            upload = self.get_uploads()[0]
            print "upload size is", len(self.get_uploads())
            print "before error1"
            print users.get_current_user().nickname()

            user = users.get_current_user()
            ancestor_key = ndb.Key('User', str(user))
            user_streams = Stream.query_stream(ancestor_key).fetch()

            for stream in user_streams:
                if stream.stream_id == self.request.get('stream_id'):
                    print 'find my stream'
                    print type(stream.blob_key)
                    stream.blob_key.insert(0, upload.key())
                    stream.num_images += 1
                    stream.last_add = str(datetime.now())
                    stream.put()

            info = {'stream_id': self.request.get('stream_id')}
            info = urllib.urlencode(info)
            self.redirect('/view_single?' + info)

        except:
            print "error!"


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/login', LoginHandler),
    ('/manage', ManageHandler),
    ('/create', CreateHandler),
    ('/view_single', ViewSingleHandler),
    ('/view', ViewAllHandler),
    ('/search', SearchHandler),
    ('/trending', TrendingHandler),
    ('/error', ErrorHandler),
    ('/create_a_new_stream', CreateANewStreamHandler),
    ('/delete_a_stream', DeleteStreamHandler),
    ('/upload_image', UploadImageHandler),
    ('/subscribe_a_stream', SubscribeStreamHandler),
    ('/unsubscribe_a_stream', UnsubscribeStreamHandler),
], debug=True)

