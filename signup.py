
import re
def escape_html(s):
    return cgi.escape(s, quote = True)


username_r = r'^[a-zA-Z0-9_-]{3,20}$'
password_r = r'^.{3,20}$'
email_r = r'^[\S]+@[\S]+\.[\S]+$'

def valid_username(s):
    return re.match(username_r, s)


def valid_password(s):
    return re.match(password_r, s)


def valid_email(s):
    return re.match(email_r, s)


def valid_match(password, verify_password):
    return password == verify_password


