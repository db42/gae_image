import cgi
import os
import png
from google.appengine.api import images
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

class Greeting(db.Model):
    author = db.UserProperty()
    content = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)
    pic = db.BlobProperty()
    
class MainPage(webapp.RequestHandler):
    def get(self):
        
        greetings_query = Greeting.all().order('-date')
        greetings = greetings_query.fetch(10)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'greetings': greetings,
            'url': url,
            'url_linktext' : url_linktext
            }

        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))
class Comparison(webapp.RequestHandler):
    def compare(self,blob):
        greetings_query = Greeting.all().order('-date')
        greetings = greetings_query.fetch(10)   
        i=0
        ds={}
        for greeting in greetings:
        #w, h, pixels, metadata = reader.read()
            temp=greeting.pic
            reader1 = png.Reader(bytes=temp)
            #w, h, pixels, metadata = reader.read()
            png_w1,png_h1,pixels1,info1 = reader1.asDirect()
            
            pixelcount = red = blue = green = 0
            #pixelcount = png_w * png_h
            i=0
            #print i 
            #print type(pixels)
            reader = png.Reader(bytes=blob)
            png_w,png_h,pixels,info = reader.asDirect()
            #print pixels
            for row in pixels:
                j=0
                #print i
                row1=pixels1.next()
                for pixel in png.group(row,info['planes']):
                    pixel1= png.group(row1,info['planes'])[j]
                    red   = red + abs(pixel[0]-pixel1[0])
                    green = green + abs(pixel[1]-pixel1[1])
                    blue  = blue + abs(pixel[2]-pixel1[2])
                    j=j+1
                i=i+1
            ds[red+green+blue]=greeting
            #print "difference",pixelcount,red,green,blue
        return ds
            
    def post(self):
        img=self.request.get('img')
        temp=db.Blob(img)
        ds=self.compare(temp)
        ds.keys().sort()
        #print ds.keys()
        greetings=[m[1] for m in ds.items()]
        
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'greetings': greetings,
            'url': url,
            'url_linktext' : url_linktext
            }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))
        
class Guestbook(webapp.RequestHandler):
    def post(self):
        greeting = Greeting()

        if users.get_current_user():
            greeting.author = users.get_current_user()
        img=self.request.get('img')
        
        greeting.pic=db.Blob(img)
        temp=greeting.pic
        #self.compare(temp)
        greeting.content = self.request.get('content')
        greeting.put()
        #self.response.out.write("completed")
        self.redirect('/')
        
class Image (webapp.RequestHandler):
    def get(self):
        greeting = db.get(self.request.get("img_id"))
        if greeting.pic:
            self.response.headers['Content-Type'] = "image/png"
            pic=images.resize(greeting.pic,32,32)
            self.response.out.write(pic)
        else:
            self.response.out.write("No image")

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/sign', Guestbook),
                                      ('/img', Image),
                                      ('/compare', Comparison)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()