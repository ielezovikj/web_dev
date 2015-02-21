

import webapp2, os, logging, cgi, re, jinja2, hashlib, hmac, random, string
from google.appengine.ext import db
from signup import *

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

secret = 'dogfood27'
def make_salt():
    res = ''
    for x in range(0, 5):
        res = res + random.choice(string.letters)
    return res

def make_pw_hash(name, pw, salt = ''):
    if salt == "":
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return "%s|%s" % (h, salt)
    
def valid_pw(name, pw, h):
    salt = h.split("|")[1]
    return make_pw_hash(name, pw, salt) == h
    

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

class User(db.Model):
    username = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    email = db.StringProperty(required = False)


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
        #self.response.headers['Content-Type'] = 'text/plain'

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
        
        self.write("\n \n <h2> You can go to /blog or /asciichan from here. <h2>")
        
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
        

class SignUp(Handler):              
    def get(self):
        self.render("signup.html")
    
    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        password = "" if not valid_password(password) else password
        verify = self.request.get("verify")
        verify = "" if not valid_match(password, verify) else verify
        email = self.request.get("email")
        username_error = "" if valid_username(username) else "That's not a valid username."
        password_error = "" if valid_password(password) else "That wasn't a valid password."
        verify_error = "" if valid_match(password, verify) else "Your passwords didn't match."
        if verify_error != "":
            password = ""

        email_error = "" if valid_email(email) or email == "" else "That's not a valid email."
        error = False
        error = (username_error != "") or (password_error != "") or (verify_error != "") or (email_error != "")
        if error:
            self.render("signup.html", username = username, password = password, verify = verify, email = email,
            username_error =  username_error, password_error = password_error, verify_error = verify_error, email_error = email_error)
        else:
            
            credentials = {}
            credentials['username'] = username
            credentials['password'] = password
            if email != "":
                credentials['email'] = email
            credentials['password'] = password_hash = make_pw_hash(username, password)
            
            new_user = User(**credentials)
            user_id = str(new_user.put().id())
            user_id_cookie = make_secure(user_id)
            self.response.headers.add_header('Set-Cookie', 'user_id = %s' % user_id_cookie)
            self.redirect("/welcome")
       
        
            
class Welcome(Handler):
    def get(self):
        user_id_cookie = self.request.cookies.get("user_id")
        user_id = user_id_cookie.split("|")[0]
        user = User.get_by_id(int(user_id))
        self.response.out.write("<h2> Welcome, " + user.username + "!</h2>")
                

app = webapp2.WSGIApplication([('/', MainPage),
("/asciichan", AsciiChan),
("/blog/newpost", NewPost),
(r'/blog/([0-9]+)', Permalink),
('/blog', Blog),
('/signup', SignUp),
('/welcome', Welcome)

], debug = True)

