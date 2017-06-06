#!/usr/bin/env python

## Title:       csToModrewrite.py
## Author:      Joe Vest
## Description: Converts Cobalt Strike profiles to Apache mod_rewrite .htaccess file format

import argparse
import sys


description = '''
Converts Cobalt Strike profiles to Apache mod_rewrite .htaccess file format 
'''

parser = argparse.ArgumentParser(description=description)
parser.add_argument('-i', dest='inputfile', help='C2 Profile file')
parser.add_argument('-c', dest='c2Server', help='C2 Server (http://teamserver)')
parser.add_argument('-d', dest='destination', help='Redirect to this URL (http:google.com)')

args = parser.parse_args()

if len(sys.argv) < 5:
    parser.print_help()
    sys.exit(1)


profile = open(args.inputfile,"r")
contents = profile.read()

# Search Strings
ua_string = "set useragent"
http_get  = "http-get"
http_post = "http-post"
set_uri   = "set uri"


# Get UserAgent
ua_start = contents.find(ua_string) + len(ua_string)
ua_end   = contents.find("\n",ua_start)
ua       = contents[ua_start:ua_end].strip()[1:-2]

# Get HTTP GET URIs
http_get_start = contents.find(http_get)
get_uri_start  = contents.find(set_uri, http_get_start) + len(set_uri)
get_uri_end    = contents.find("\n", get_uri_start) 
get_uri        = contents[get_uri_start:get_uri_end].strip()[1:-2]

# Get HTTP POST URIs
http_post_start = contents.find(http_post)
post_uri_start  = contents.find(set_uri, http_post_start) + len(set_uri)
post_uri_end    = contents.find("\n", post_uri_start) 
post_uri        = contents[post_uri_start:post_uri_end].strip()[1:-2]

# Create URIs list
get_uris  = get_uri.split()
post_uris = post_uri.split()
uris = get_uris + post_uris

# Create UA in modrewrite syntax
ua_string = ua.replace(' ','\ ').replace('.','\.')


# Create URI string in modrewrite syntax
uris_string = "|".join(uris)


htaccess_template = '''
RewriteEngine On
RewriteCond %{{REQUEST_URI}} ^/({})/?$
RewriteCond %{{HTTP_USER_AGENT}} ^{})?$
RewriteRule ^.*$ {}{{REQUEST_URI}} [P]
RewriteRule ^.*$ {}/? [L,R=302]
'''

print("")
print("#### SAVE THE FOLLOWING AS .htaccess ####")
print(htaccess_template.format(uris_string,ua_string,args.c2Server,args.destination))
