#!/usr/bin/env python

import sys
import ConfigParser
import optparse

import simplejson
import pysolr
import Flickr.API

class SimpleFlickr :

    def __init__ (self, cfg) :

	key = cfg.get('flickr', 'api_key')
        secret = cfg.get('flickr', 'api_secret')
        
	api = Flickr.API.API(key, secret)

    	self.cfg = cfg
        self.api = api
        
    def api_call (self, method, **args) :

        token = self.cfg.get('flickr', 'auth_token')

        args['auth_token'] = token
        args['format'] = 'json'
        args['nojsoncallback'] = 1

        try :
		req = Flickr.API.Request(method=method, **args)
		res = self.api.execute_request(req)	
		json = simplejson.loads(res.read())
       	except Exception, e :
        	return None

        if not json.has_key('stat') :
            	return None
        
        if json['stat'] != 'ok' :
        	return None

        return json

class Flolr (SimpleFlickr) :

    def __init__ (self, cfg) :

    	SimpleFlickr.__init__(self, cfg)

        # solr stuff here...

        self.docs = []
        
    def get_nsid (self) :
    
	json = self.api_call('flickr.auth.checkToken')
	nsid = json['auth']['user']['nsid']
	return nsid

    def get_photos (self) :

	nsid = self.get_nsid()
        
        pages = None
        page = 1

	# GET datelastupdate here...
        
	args = {
            'user_id' : nsid,
            'per_page' : 10,
            }

        docs = []
        
        while not pages or page <= pages :

		args['page'] = page

        	json = self.api_call('flickr.photos.search', **args)

                if not pages :
                    	pages = json['photos']['pages']
	
                        if pages == 0 :
                            break

		for ph in json['photos']['photo'] :
			self.ensolrify(ph['id'])
                        
                self.index_photos()
                docs = []
                
                page += 1
                break

    def ensolrify (self, photo_id) :

    		photo = self.api_call('flickr.photos.getInfo', photo_id=photo_id)

                if not photo :
                	return False

                doc = {}
                self.docs.append(doc)
    
    def index_photos (self) :

	        # self.solr.add(self.docs)
    		self.docs = []
                 
if __name__ == '__main__' :

	parser = optparse.OptionParser()
        parser.add_option("-c", "--config", dest="config", help="The path to an ini config file with your Flickr API key")
        
	(opts, args) = parser.parse_args()
        
	cfg = ConfigParser.ConfigParser()
	cfg.read(opts.config)

	fl = Flolr(cfg)
	fl.get_photos()
