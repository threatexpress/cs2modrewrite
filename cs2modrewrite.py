#!/usr/bin/env python

## Title:       csToModrewrite.py
## Author:      Joe Vest, Andrew Chiles
## Description: Converts Cobalt Strike profiles to Apache mod_rewrite .htaccess file format

import argparse
import sys


description = '''
Converts Cobalt Strike profiles to Apache mod_rewrite .htaccess file format by using the User-Agent and URI Endpoint to create rewrite rules.  Make sure the profile passes a c2lint check before running this script.
'''

parser = argparse.ArgumentParser(description=description)
parser.add_argument('-i', dest='inputfile', help='C2 Profile file')
parser.add_argument('-c', dest='c2Server', help='C2 Server (http://teamserver)')
parser.add_argument('-d', dest='destination', help='(Optional) Redirect to this URL (http://google.com)')

args = parser.parse_args()

# Check Arguments
if not args.inputfile:  
    print("[!] Missing inputfile")
    parser.print_help()
    sys.exit(1)

if not args.c2Server:   
    print("[!] Missing c2Server")
    parser.print_help()
    sys.exit(1)

if not args.destination:    
    print("[!] Missing destination")
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

# Errors
errorfound = False
errors = "\n##########\n[!] ERRORS\n"

# Get UserAgent
if contents.find(ua_string) == -1:
    ua = ""
    errors += "[!] User-Agent Not Found\n"
    errorfound = True
else:
    ua_start = contents.find(ua_string) + len(ua_string)
    ua_end   = contents.find("\n",ua_start)
    ua       = contents[ua_start:ua_end].strip()[1:-2]


# Get HTTP GET URIs
http_get_start = contents.find(http_get)
if contents.find(set_uri) == -1: 
    get_uri = ""
    errors += "[!] GET URIs Not Found\n"
    errorfound = True
else:
    get_uri_start  = contents.find(set_uri, http_get_start) + len(set_uri)
    get_uri_end    = contents.find("\n", get_uri_start)
    get_uri        = contents[get_uri_start:get_uri_end].strip()[1:-2]

# Get HTTP POST URIs
http_post_start = contents.find(http_post)
if contents.find(set_uri) == -1:
    post_uri = ""
    errors += "[!] POST URIs Not Found\n"
    errorfound = True
else:
    post_uri_start  = contents.find(set_uri, http_post_start) + len(set_uri)
    post_uri_end    = contents.find("\n", post_uri_start)
    post_uri        = contents[post_uri_start:post_uri_end].strip()[1:-2]

# Get HTTP Stager URIs x86
http_stager_start = contents.find(http_stager)
if contents.find(set_uri_86) == -1:
    stager_uri_86 = ""
    errors += "[!] x86 Stager URIs Not Found\n"
    errorfound = True
else:
    stager_uri_start  = contents.find(set_uri_86, http_stager_start) + len(set_uri_86)
    stager_uri_end    = contents.find("\n", stager_uri_start)
    stager_uri_86     = contents[stager_uri_start:stager_uri_end].strip()[1:-2]

# Get HTTP Stager URIs x64
http_stager_start = contents.find(http_stager)
if contents.find(set_uri_64) == -1:
    stager_uri_64 = ""
    errors += "[!] x86 Stager URIs Not Found\n"
    errorfound = True
else:
    stager_uri_start  = contents.find(set_uri_64, http_stager_start) + len(set_uri_64)
    stager_uri_end    = contents.find("\n", stager_uri_start)
    stager_uri_64     = contents[stager_uri_start:stager_uri_end].strip()[1:-2]

# Create URIs list
get_uris  = get_uri.split()
post_uris = post_uri.split()
stager86_uris = stager_uri_86.split()
stager64_uris = stager_uri_64.split()
uris = get_uris + post_uris + stager86_uris + stager64_uris

# Create UA in modrewrite syntax. No regex needed in UA string matching, but () characters must be escaped
ua_string = ua.replace('(','\(').replace(')','\)')

# Create URI string in modrewrite syntax. "*" are needed in REGEX to support GET parameters on the URI
uris_string = ".*|".join(uris) + ".*"



htaccess_template = '''
########################################
## .htaccess START 
RewriteEngine On

## (Optional)
## Scripted Web Delivery 
## Uncomment and adjust as needed
#RewriteCond %{{REQUEST_URI}} ^/css/style1.css?$
#RewriteCond %{{HTTP_USER_AGENT}} ^$
#RewriteRule ^.*$ "http://TEAMSERVER%{{REQUEST_URI}}" [P,L]

## Default Beacon Staging Support (/1234)
RewriteCond %{{REQUEST_URI}} ^/..../?$
RewriteCond %{{HTTP_USER_AGENT}} "{ua}"
RewriteRule ^.*$ "http://TEAMSERVER%{{REQUEST_URI}}" [P,L]

## C2 Traffic (HTTP-GET, HTTP-POST, HTTP-STAGER URIs)
## Logic: If a requested URI AND the User-Agent matches, proxy the connection to the Teamserver
## Consider adding other HTTP checks to fine tune the check.  (HTTP Cookie, HTTP Referer, HTTP Query String, etc)
## Refer to http://httpd.apache.org/docs/current/mod/mod_rewrite.html
## Profile URIs
RewriteCond %{{REQUEST_URI}} ^({uris})$
## Profile UserAgent
RewriteCond %{{HTTP_USER_AGENT}} "{ua}"
RewriteRule ^.*$ "{c2server}%{{REQUEST_URI}}" [P,L]

## Redirect all other traffic here
RewriteRule ^.*$ {destination}/? [L,R=302]

## .htaccess END
########################################
'''
print("#### Save the following as .htaccess in the root web directory")
print(htaccess_template.format(uris=uris_string,ua=ua_string,c2server=args.c2Server,destination=args.destination))


# Print Errors Found
if errorfound: print(errors)
