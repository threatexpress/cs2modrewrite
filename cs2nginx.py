#!/usr/bin/env python

## Title:       cs2nginx.py
## Author:      Joe Vest, Andrew Chiles
## Description: Converts Cobalt Strike profiles to Nginx config file format (/etc/nginx/nginx.conf)

import argparse
import sys
import re

description = '''
Converts Cobalt Strike profiles by using URI endpoints to create regex matching rules.
This version does not currently contain User-Agent matching.
Make sure the profile passes a c2lint check before running this script.

The resulting Nginx config will:
- Attempt to serve files locally if they exist
- Proxy any matching URIs to the C2 server
- Redirect any non-matching requests to a specified server
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
    print("\n[!] c2server is malformed. Are you sure {} is a valid URL?".format(args.c2server))
    sys.exit(1)

if re.match(regex, args.redirect) is None:
    parser.print_help()
    print("\n[!] redirect is malformed. Are you sure {} is a valid URL?".format(args.redirect))
    sys.exit(1)


# Read C2 profile
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
    errors += "[!] x64 Stager URIs Not Found\n"
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

nginx_template = '''
########################################
## /etc/nginx/nginx.conf START
user www-data;
worker_processes 4;
pid /run/nginx.pid;

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
    log_format   main '$remote_addr - $remote_user [$time_local]  $status '
    '"$request" $body_bytes_sent "$http_referer" '
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
        error_page 400 401 402 403 404 405 406 407 408 409 410 411 412 413 414 415 416 417 418 420 422 423 424 426 428 429 431 444 449 450 451 500 501 502 503 504 505 506 507 508 509 510 511 $scheme://$host;

        ##########################
        # Generic file request handling
        ##########################
        # Try to serve static file and send to @redirect location if not present
        location / {{
            try_files $uri @redirect;
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

        # Process PHP file requests
        location ~ \.php$ {{
                try_files       $uri @c2;
                fastcgi_pass    unix:/var/run/php5-fpm.sock;
                fastcgi_index   index.php;
                fastcgi_param   SCRIPT_FILENAME     $document_root$fastcgi_script_name;
                include         fastcgi_params;
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
print(nginx_template.format(uris=uris_string,ua=ua_string,c2server=args.c2server,redirect=args.redirect,hostname=args.hostname))

# Print Errors Found
if errorfound: print(errors)
