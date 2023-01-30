#!/usr/bin/env python

## Title:       cs2modrewrite.py
## Author:      Joe Vest, Andrew Chiles

import argparse
import re
import sys

description = """
Python 3.0+
Converts Cobalt Strike (>=4.0) profiles to Apache mod_rewrite .htaccess file format by using the User-Agent and URI Endpoint to create rewrite rules.
Make sure the profile passes a c2lint check before running this script.
"""

parser = argparse.ArgumentParser(description=description)
parser.add_argument("-i", dest="inputfile", help="C2 Profile file", required=True)
parser.add_argument(
    "-c", dest="c2server", help="C2 Server (e.g., http://C2SERVER)", required=True
)
parser.add_argument(
    "-r",
    dest="redirect",
    help="Redirect to this URL (e.g., http://google.com)",
    required=True,
)
parser.add_argument(
    "-o",
    dest="out_file",
    help="Write .htaccess contents to target file",
    required=False,
)

args = parser.parse_args()

# Make sure we were provided with vaild URLs
# https://stackoverflow.com/questions/7160737/python-how-to-validate-a-url-in-python-malformed-or-not
regex = re.compile(
    r"^(?:http|ftp)s?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)

if re.match(regex, args.c2server) is None:
    parser.print_help()
    print(
        "[!] c2server is malformed. Are you sure {} is a valid URL?".format(
            args.c2server
        ),
        file=sys.stderr,
    )
    sys.exit(1)

if re.match(regex, args.redirect) is None:
    parser.print_help()
    print(
        "[!] redirect is malformed. Are you sure {} is a valid URL?".format(
            args.redirect
        ),
        file=sys.stderr,
    )
    sys.exit(1)

profile = open(args.inputfile, "r")
contents = profile.read()

# Strip all single line comments (#COMMENT\n) from profile before searching so it doesn't break our crappy parsing
contents = re.sub(re.compile("#.*?\n"), "\n", contents)

# Search Strings
set_ua_search_string = r"set useragent *\"(.*?)\"\;"
set_uri = r"set uri.*\"(.*?)\"\;"
# Additional UA strings could be added with the `header` option
header_ua_search_string = r"header \"User-Agent\".*\"(.*?)\"\;"

# Errors
errorfound = False
errors = "\n##########\n[!] ERRORS\n"

# Get Default UserAgent
if len(re.findall(set_ua_search_string, contents)) == 0:
    uas = []
    errors += "[!] Default User-Agent Not Found\n"
    errorfound = True
else:
    uas = re.findall(set_ua_search_string, contents)

# Get all UserAgents set via the `header` option and add them to our list of UserAgents
for ua in re.findall(header_ua_search_string, contents):
    uas.append(ua)

# Get all profile URIs based on our regex
if len(re.findall(set_uri, contents)) == 0:
    uris = ""
    errors += "[!] No URIs found\n"
    errorfound = True
else:
    uris = re.findall(set_uri, contents)
    # Split any uri specifications to handle cases where multiple URIs are separated by whitespace
    # i.e. set uri "/path/1 /path/2"
    split_uris = []
    for uri in uris:
        for i in uri.split():
            split_uris.append(i)
    # Remove any duplicate URIs
    uris = list(set(split_uris))

# Create UA in modrewrite syntax. No regex needed in UA string matching, but () characters must be escaped
uas = [(ua).replace("(", "\(").replace(")", "\)") for ua in uas]
# Add | separator between multiple User-Agents for modrewrite
uas_string = "|".join(uas)

# Create URI string in modrewrite syntax. "*" are needed in regex to support GET and uri-append parameters on the URI
uris_string = ".*|".join(uris) + ".*"

# Check if staging is disabled, and adjust staging section for template
if bool(re.search('host_stage "false"', contents)):
    staging = ""
else:
    staging = """
## Default Beacon Staging Support (/1234)
RewriteCond %{{REQUEST_METHOD}} GET [NC]
RewriteCond %{{REQUEST_URI}} ^/..../?$
RewriteCond %{{HTTP_USER_AGENT}} "^({uas})$"
RewriteRule ^.*$ "{c2server}%{{REQUEST_URI}}" [P,L]
"""
    # Replace variables in staging block
    staging = staging.format(uas=uas_string, c2server=args.c2server)

htaccess_template = """
########################################
## .htaccess START
RewriteEngine On

## (Optional)
## Scripted Web Delivery
## Uncomment and adjust as needed
#RewriteCond %{{REQUEST_URI}} ^/css/style1.css?$
#RewriteCond %{{HTTP_USER_AGENT}} ^$
#RewriteRule ^.*$ "http://TEAMSERVER%{{REQUEST_URI}}" [P,L]
{staging}
## C2 Traffic (HTTP-GET, HTTP-POST, HTTP-STAGER URIs)
## Logic: If a requested URI AND the User-Agent matches, proxy the connection to the Teamserver
## Consider adding other HTTP checks to fine tune the check.  (HTTP Cookie, HTTP Referer, HTTP Query String, etc)
## Refer to http://httpd.apache.org/docs/current/mod/mod_rewrite.html
## Only allow GET and POST methods to pass to the C2 server
RewriteCond %{{REQUEST_METHOD}} ^(GET|POST) [NC]
## Profile URIs
RewriteCond %{{REQUEST_URI}} ^({uris})$
## Profile UserAgents
RewriteCond %{{HTTP_USER_AGENT}} "^({uas})$"
RewriteRule ^.*$ "{c2server}%{{REQUEST_URI}}" [P,L]

## Redirect all other traffic here
RewriteRule ^.*$ {redirect}/? [L,R=302]

## .htaccess END
########################################
"""
print("#### Save the following as .htaccess in the root web directory")
print("## Profile User-Agent Found ({}):".format(str(len(uas))))
for ua in uas:
    print("# {}".format(ua))
print("## Profile URIS Found ({}):".format(str(len(uris))))
for uri in uris:
    print("# {}".format(uri))

htaccess = htaccess_template.format(
    uris=uris_string,
    uas=uas_string,
    c2server=args.c2server,
    redirect=args.redirect,
    staging=staging,
)
if args.out_file:
    with open(args.out_file, "w") as outfile:
        outfile.write(htaccess)
else:
    print(htaccess)

# Print Errors Found
if errorfound:
    print(errors, file=sys.stderr)
