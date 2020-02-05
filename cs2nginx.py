#!/usr/bin/env python

## Title:       cs2nginx.py
## Author:      Joe Vest, Andrew Chiles
## Description: Converts Cobalt Strike profiles to Nginx config file format (/etc/nginx/nginx.conf)

import argparse
import sys
import re

description = '''
Requires Python 3.0+
Converts Cobalt Strike malleable C2 profiles (<=4.0) by using URI endpoints to create regex matching rules.
This version does not currently contain User-Agent matching.
Make sure the profile passes a c2lint check before running this script.

The resulting Nginx config will:
- Attempt to serve files locally if they exist
- Proxy any matching URIs to the C2 server
- Redirect any non-matching requests to a specified redirection domain along with the original URI
'''

parser = argparse.ArgumentParser(description=description)
parser.add_argument('-i', dest='inputfile', help='C2 Profile file', required=True)
parser.add_argument('-c', dest='c2server', help='C2 Server URL (e.g., http://teamserver_ip or https://teamserver_domain)', required=True)
parser.add_argument('-r', dest='redirect', help='Redirect non-matching requests to this URL (http://google.com)', required=True)
parser.add_argument('-H', dest='hostname', help='Hostname for Nginx redirector', required=True)

args = parser.parse_args()

# Make sure we were provided with vaild URLs 
# https://stackoverflow.com/questions/7160737/python-how-to-validate-a-url-in-python-malformed-or-not
regex = re.compile(
    r'^(?:http|ftp)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
    r'localhost|' #localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?' # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

if re.match(regex, args.c2server) is None:
    parser.print_help()
    print("[!] c2server is malformed. Are you sure {} is a valid URL?".format(args.c2server),file=sys.stderr)
    sys.exit(1)

if re.match(regex, args.redirect) is None:
    parser.print_help()
    print("[!] redirect is malformed. Are you sure {} is a valid URL?".format(args.redirect),file=sys.stderr)
    sys.exit(1)

# Read C2 profile
profile = open(args.inputfile,"r")
contents = profile.read()

# Strip all single line comments (#COMMENT\n) from profile before searching so it doens't break our crappy parsing
contents = re.sub(re.compile("#.*?\n" ) ,"" ,contents)

# Search Strings
ua_string  = "set useragent"
set_uri    = r"set uri.*\"(.*?)\"\;"

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

# Get all profile URIs based on our regex
if len(re.findall(set_uri,contents)) == 0:
    uris = ""
    errors += "[!] No URIs found\n"
    errorfound = True
else:
    uris = re.findall(set_uri,contents)
    # Split any uri specifications to handle cases where multiple URIs are separated by whitespace
    # i.e. set uri "/path/1 /path/2"
    split_uris = []
    for uri in uris:
        for i in uri.split():  
            split_uris.append(i)
    # Remove any duplicate URIs
    uris = list(set(split_uris))

# Create UA in modrewrite syntax. No regex needed in UA string matching, but () characters must be escaped
ua_string = ua.replace('(','\(').replace(')','\)')

# Create URI string in modrewrite syntax. "*" are needed in regex to support GET and uri-append parameters on the URI
uris_string = ".*|".join(uris) + ".*"

nginx_template = '''
########################################
## /etc/nginx/nginx.conf START
user www-data;
worker_processes 4;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {{
    worker_connections 768;
    # multi_accept on;
}}

http {{

    ############################
    # Basic Settings
    ############################

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Disable detailed NGINX "Server" header
    server_tokens off;
    more_set_headers 'Server: Server';
    # Disable referrers when we redirect useragents away from this server
    add_header Referrer-Policy "no-referrer";

    # server_names_hash_bucket_size 64;
    # server_name_in_redirect off;

    include /etc/nginx/mime.types;
    default_type text/html;

    ############################
    # SSL Settings
    ############################

    ssl_protocols TLSv1 TLSv1.1 TLSv1.2; # Dropping SSLv3, ref: POODLE
    ssl_prefer_server_ciphers on;

    ############################
    # Logging Settings
    #############################
    log_format main '[$time_iso8601] $remote_addr - $remote_user  proxy:$upstream_addr $status '
                    '"$request" $body_bytes_sent "$http_referer"'
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    #############################
    # Compression
    ##############################
    # Disable GZIP compression to prevent C2 errors
    gzip off;
    gzip_disable "msie6";

    ############################
    # HTTP server block with reverse-proxy 
    ############################

    server {{
        #########################
        # Custom server variables
        #########################
        set $C2_SERVER {c2server};
        set $REDIRECT_DOMAIN {redirect};
        server_name {hostname};

        #########################
        # Listening ports
        #########################
        listen 80;
        listen [::]:80;
        
        #####################
        # SSL Configuration
        #####################
        #listen 443 ssl;
        #listen [::]:443 ssl;
        #ssl on;

        #ssl_certificate /etc/letsencrypt/live/<DOMAIN_NAME>/fullchain.pem; # managed by Certbot
        #ssl_certificate_key /etc/letsencrypt/live/<DOMAIN_NAME>/privkey.pem; # managed by Certbot
        #ssl_session_cache shared:le_nginx_SSL:1m; # managed by Certbot
        #ssl_session_timeout 1440m; # managed by Certbot
        #ssl_protocols TLSv1 TLSv1.1 TLSv1.2; # managed by Certbot
        #ssl_prefer_server_ciphers on; # managed by Certbot

        #########################################
        # Server root directory for serving files
        #########################################
        root /var/www/html;
        index index.html;
        
        ##########################
        # Error handling
        ##########################
        # Set all custom error pages to redirect back to the $host from the requested URI
        # This should return to the useragent to the server root and avoid presentation of default Nginx error pages
        error_page 400 401 402 403 404 405 406 407 408 409 410 411 412 413 414 415 416 417 418 420 422 423 424 426 428 429 431 444 449 450 451 500 501 502 503 504 505 506 507 508 509 510 511 @redirect;

        ##########################
        # Generic file request handling
        ##########################
        # Try to serve static file from server root
        # Try to serve index.html if present
        # Send to @redirect location
        location / {{
            try_files $uri $uri/ /index.html @redirect;
        }}

        ##########################
        # C2 Profile endpoints
        ##########################
        # Custom regex to allow requests to backend C2 server
        # Note: If the backend C2 server isn't available, the useragent will receive a redirect to the 
        #       redirector's root page due to the custom error handling configured above
        # Note: This intentionally does not handle default Beacon staging ^/....
        location ~ ^({uris})$ {{
            proxy_pass          $C2_SERVER;
        
            # If you want to pass the C2 server's "Server" header through then uncomment this line
            # proxy_pass_header Server;
            expires             off;
            proxy_redirect      off;
            proxy_set_header    Host                $host;
            proxy_set_header    X-Forwarded-For     $proxy_add_x_forwarded_for;
            proxy_set_header    X-Real-IP           $remote_addr;
        }}

        # Redirect requests to the $REDIRECT_DOMAIN + Original request URI
        location @redirect {{
        	return 302 $REDIRECT_DOMAIN$request_uri;
        }}

        # Alernative method to redirect any request for a file not present on the Nginx server to the C2 server
        # Note: This is not as secure and doesn't provide much protection for the C2 server from scanning
        #location / {{
        #   try_files $uri $uri/ @c2;
        #}}

        #location @c2 {{
        #        proxy_pass         $C2_SERVER;
        #        # If you want to pass the C2 server's "Server" header through then uncomment this line
        #        # proxy_pass_header Server;
        #        expires            off;
        #        proxy_redirect     off;
        #        proxy_set_header   Host                $host;
        #        proxy_set_header   X-Forwarded-For     $proxy_add_x_forwarded_for;
        #        proxy_set_headerX-Real-IP              $remote_addr;
        #}}
	}}
}}
## /etc/nginx/nginx.conf END
########################################
'''
print("#### Save the following as /etc/nginx/nginx.conf")
print("## Profile User-Agent Found:")
print("# {}".format(ua))
print("## Profile URIS Found ({}):".format(str(len(uris))))
for uri in uris: 
    print("# {}".format(uri))
print(nginx_template.format(uris=uris_string,ua=ua_string,c2server=args.c2server,redirect=args.redirect,hostname=args.hostname))

# Print Errors Found
if errorfound: 
    print(errors, file=sys.stderr)
