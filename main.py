

import webapp2, os, logging
import jinja2, hashlib, hmac
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

secret = 'dogfood27'
def hash_str(s):
    return hmac.new(secret, s, hashlib.sha256).hexdigest()

def make_secure(value):
    return "%s|%s" %(value, hash_str(value))

def check_secure_val(h):
    if h == None:
        return None
    value = h.split('|')[0]
    if h == make_secure(value):
        return value




class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        #it returns a string
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))



class Art(db.Model):
    title = db.StringProperty(required = True)
    art = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

class BlogPost(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)


class AsciiChan(Handler):
    def render_front(self, title = "", art = "", error = ""):
        arts = db.GqlQuery("select * from Art order by created desc")

        self.render("front_ascii.html", title = title, art = art, error = error, arts = arts)
    def get(self):
        self.render_front()

    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")
        if title and art:
            a = Art(title = title, art = art)
            a.put()
            self.redirect("/asciichan")
        else:
            error = "We both need a title and some artwork!"
            self.render_front(title, art, error = error)




class MainPage(Handler):
    def get(self):
        #self.write("<h1> You can go to /asciichan or /blog .</h1>")
        self.response.headers['Content-Type'] = 'text/plain'

        visits = self.request.cookies.get('visits')
        num_of_visits = 0
        visits_so_far = check_secure_val(visits)
        if visits and visits_so_far:
            num_of_visits = int(visits_so_far)
        num_of_visits += 1
        new_visits_cookie = make_secure(str(num_of_visits))
        self.response.headers.add_header('Set-Cookie', 'visits = %s' % new_visits_cookie)

        if num_of_visits > 1000:
            self.write("You are the best ever.")
        else:
            self.write("You've been here %s times." % num_of_visits)
class NewPost(Handler):
    def get(self):
        self.render("newpost.html")
    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")
        if subject and content:
            new_blog_post = BlogPost(subject = subject, content = content)
            key = new_blog_post.put()
            #Here we wanna redirect to a permalink.
            self.redirect("/blog/%s" % str(key.id()))
        else:
            error = "You need a subject and some content to post."
            self.render("newpost.html", error = error)

class Blog(Handler):
    def get(self):
        posts = db.GqlQuery("select * from BlogPost order by created desc")
        self.render("front_blog.html", posts = posts)

class Permalink(Handler):
    def get(self, id):
        post = BlogPost.get_by_id(int(id))
        self.render("permalink.html", subject = post.subject, content = post.content, created = post.created)

app = webapp2.WSGIApplication([('/', MainPage),
("/asciichan", AsciiChan),
("/blog/newpost", NewPost),
(r'/blog/([0-9]+)', Permalink),
('/blog', Blog),
], debug = True)
