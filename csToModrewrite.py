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
ua_string  = "set useragent"
http_get   = "http-get"
http_post  = "http-post"
set_uri    = "set uri"

http_stager = "http-stager"
set_uri_86 = "set uri_x86" 
set_uri_64 = "set uri_x64" 


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

# Get HTTP Stater URIs x86
http_stager_start = contents.find(http_stager)
stager_uri_start  = contents.find(set_uri_86, http_stager_start) + len(set_uri_86)
stager_uri_end    = contents.find("\n", stager_uri_start) 
stager_uri_86     = contents[stager_uri_start:stager_uri_end].strip()[1:-2]

# Get HTTP Stater URIs x64
http_stager_start = contents.find(http_stager)
stager_uri_start  = contents.find(set_uri_64, http_stager_start) + len(set_uri_64)
stager_uri_end    = contents.find("\n", stager_uri_start) 
stager_uri_64     = contents[stager_uri_start:stager_uri_end].strip()[1:-2]

# Create URIs list
get_uris  = get_uri.split()
post_uris = post_uri.split()
stager86_uris = stager_uri_86.split()
stager64_uris = stager_uri_64.split()
uris = get_uris + post_uris + stager86_uris + stager64_uris

print(uris)

# Create UA in modrewrite syntax
ua_string = ua.replace(' ','\ ').replace('.','\.')

# Create URI string in modrewrite syntax
uris_string = "|".join(uris)

htaccess_template = '''

RewriteEngine On

# Scripted Web Delivery (Optional)
# Uncomment and adjust as needed
#RewriteCond %{{REQUEST_URI}} ^/imgs/logo1.png?$
#RewriteCond %{{HTTP_USER_AGENT}} ^$
#RewriteRule ^.*$ http://TEAMSERVER%{{REQUEST_URI}} [P]
#RewriteCond %{{REQUEST_URI}} ^/..../?$

# C2 Traffic (HTTP-GET, HTTP-POST, HTTP-STAGER URIs) 
RewriteCond %{{REQUEST_URI}} ^/({})/?$
RewriteCond %{{HTTP_USER_AGENT}} ^{})?$
RewriteRule ^.*$ {}{{REQUEST_URI}} [P]

# Redirect All other traffic here
RewriteRule ^.*$ {}/? [L,R=302]
'''

print("")
print("#### SAVE THE FOLLOWING AS .htaccess ####")
print(htaccess_template.format(uris_string,ua_string,args.c2Server,args.destination))
