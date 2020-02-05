# Automatically Generate Rulesets for Apache mod_rewrite or Nginx for Intelligent HTTP C2 Redirection

This project converts a Cobalt Strike profile to a functional mod_rewrite `.htaccess` or Nginx config file to support HTTP reverse proxy redirection to a Cobalt Strike teamserver. The use of reverse proxies provides protection to backend C2 servers from profiling, investigation, and general internet background radiation.

***Note***: You should test and tune the output as needed before deploying, but these scripts should handle the heavy lifting.

## Features

- Now requires Python 3.0+ (this is 2020 after all)
- Supports the Cobalt Strike custom URI features as of CS 4.0
- Rewrite Rules based on valid C2 URIs (HTTP GET, POST, and Stager) and specified User-Agent string.
  - Result: Only requests to valid C2 endpoints with a specified UA string will be proxied to the Team Server by default.
- Uses a custom Malleable C2 profile to build a .htaccess file with corresponding mod_rewrite rules
- Uses a custom Malleable C2 profile to build a Nginx config with corresponding proxy_pass rules
- HTTP or HTTPS proxying to the Cobalt Strike Team Server
- HTTP 302 Redirection to a Legitimate Site for Non-Matching Requests

## Quick start

The havex.profile example is included for a quick test.

1) Run the script against a profile
2) Save the output to `.htaccess` or `/etc/nginx/nginx.conf` on your redirector
3) Modify as needed
4) Reload\restart the web server

## Apache mod_rewrite Example Usage

    python3 cs2modrewrite.py -i havex.profile -c https://TEAMSERVER -r https://GOHERE > /var/www/html/.htaccess
    #### Save the following as .htaccess in the root web directory (i.e. /var/www/html/.htaccess)
    
    ########################################
    ## .htaccess START 
    RewriteEngine On
<<<<<<< HEAD
=======
    ## Uncomment to enable verbose debugging in /var/logs/apache2/error.log
    # LogLevel alert rewrite:trace5
>>>>>>> a3865dd3273a1d8f4f7a0a2899f2388f8e1f5547
    
    ## (Optional)
    ## Scripted Web Delivery 
    ## Uncomment and adjust as needed
    #RewriteCond %{REQUEST_URI} ^/css/style1.css?$
    #RewriteCond %{HTTP_USER_AGENT} ^$
    #RewriteRule ^.*$ "http://TEAMSERVER%{REQUEST_URI}" [P,L]
    
    ## Default Beacon Staging Support (/1234)
    RewriteCond %{REQUEST_URI} ^/..../?$
    RewriteCond %{HTTP_USER_AGENT} "Mozilla/5.0 \(Windows; U; MSIE 7.0; Windows NT 5.2\) Java/1.5.0_08"
    RewriteRule ^.*$ "http://TEAMSERVER%{REQUEST_URI}" [P,L]
    
    ## C2 Traffic (HTTP-GET, HTTP-POST, HTTP-STAGER URIs)
    ## Logic: If a requested URI AND the User-Agent matches, proxy the connection to the Teamserver
    ## Consider adding other HTTP checks to fine tune the check.  (HTTP Cookie, HTTP Referer, HTTP Query String, etc)
    ## Refer to http://httpd.apache.org/docs/current/mod/mod_rewrite.html
    ## Profile URIs
    RewriteCond %{REQUEST_URI} ^(/include/template/isx.php.*|/wp06/wp-includes/po.php.*|/wp08/wp-includes/dtcla.php.*|/modules/mod_search.php.*|/blog/wp-includes/pomo/src.php.*|/includes/phpmailer/class.pop3.php.*|/api/516280565958.*|/api/516280565959.*)$
    ## Profile UserAgent
    RewriteCond %{HTTP_USER_AGENT} "Mozilla/5.0 \(Windows; U; MSIE 7.0; Windows NT 5.2\) Java/1.5.0_08"
    RewriteRule ^.*$ "https://TEAMSERVER%{REQUEST_URI}" [P,L]
    
    ## Redirect all other traffic here (Optional)
    RewriteRule ^.*$ HTTPS://GOHERE/ [L,R=302]
    
    ## .htaccess END
    ########################################

### Apache Rewrite Setup and Tips

<<<<<<< HEAD
Install apache and enable\disable appropriate modules
=======
    python ./cs2nginx.py -i havex.profile -c https://127.0.0.1 -r https://www.google.com -H mydomain.local
    
    python ./cs2nginx.py -h
    usage: cs2nginx.py [-h] [-i INPUTFILE] [-c C2SERVER] [-r REDIRECT]
                    [-H HOSTNAME]

    Converts Cobalt Strike profiles to Nginx proxy_pass format by using URI
    endpoints to create regex matching rules. Make sure the profile passes a
    c2lint check before running this script.

    optional arguments:
    -h, --help      show this help message and exit
    -i INPUTFILE    C2 Profile file
    -c C2SERVER     C2 Server (http://teamserver_ip or
                    https://teamserver_domain)
    -r REDIRECT     Redirect bad requests to this URL (http://google.com)
    -H HOSTNAME     Hostname for Nginx redirector


----------------------------------------------
## Nginx Setup

`apt-get install nginx nginx-extras`

*Note:* `nginx-extras` is needed for custom server headers. If you can't get this package, then comment out the server header line in the resulting configuration file.
 
## Apache Rewrite Setup and Tips

### Enable Rewrite and Proxy
>>>>>>> a3865dd3273a1d8f4f7a0a2899f2388f8e1f5547

    apt-get install apache2
    a2enmod rewrite headers proxy proxy_http ssl cache
    a2dismod -f deflate
    service apache2 reload

*Note:* https://bluescreenofjeff.com/2016-06-28-cobalt-strike-http-c2-redirectors-with-apache-mod_rewrite/
"e0x70i pointed out in the comments below that if your Cobalt Strike Malleable C2 profile contains an Accept-Encoding header for gzip, your Apache install may compress that traffic by default and cause your Beacon to be unresponsive or function incorrectly. To overcome this, disable mod_deflate (via a2dismod deflate and add the No Encode ([NE]) flag to your rewrite rules. (Thank you, e0x70i!)"

<<<<<<< HEAD
### Enable SSL support

Ensure the following entries are in the site's config (i.e. `/etc/apache2/available-sites/*.conf`)
=======
### SSL support requires the following in the site config
>>>>>>> a3865dd3273a1d8f4f7a0a2899f2388f8e1f5547

    # Enable SSL
    SSLEngine On
    
    # Enable Proxy
    SSLProxyEngine On
<<<<<<< HEAD
    # Trust Self-Signed Certificates generated by CobaltStrike
=======
    
    # Trust Self-Signed Certificates
>>>>>>> a3865dd3273a1d8f4f7a0a2899f2388f8e1f5547
    SSLProxyVerify none
    SSLProxyCheckPeerCN off
    SSLProxyCheckPeerName off
    SSLProxyCheckPeerExpire off

### .HTACCESS

If you plan on using mod_rewrite in .htaccess files (instead of the site's config file), you also need to enable the use of `.htaccess` files by changing `AllowOverride None` to `AllowOverride All`. For all websites, edit `/etc/apache2/apache.conf`

    <Directory /var/www/>
        Options FollowSymLinks MultiViews
        AllowOverride All
        Order allow,deny
        allow from all
    </Directory>

Finally, restart apache once more for good measure.

`service apache2 restart`

### Troubleshooting

If you need to troubleshoot redirection rule behavior, enable detailed error tracing in your site's configuration file by adding the following line.

`LogLevel alert rewrite:trace5`

Next, reload apache, and monitor `/var/log/access.log` `/var/log/error.log` to see which rules are matching.

----------------------------------------------

## Nginx Example Usage

### Install Nginx

    apt-get install nginx

### Create Redirection Rules

Save the cs2nginx.py output to `/etc/nginx/nginx.conf` and modify as needed (SSL parameters).

`python3 ./cs2nginx.py -i havex.profile -c https://127.0.0.1 -r https://www.google.com -H mydomain.local >/etc/nginx/nginx.conf`

Finally, restart nginx after modifying the server configuration file.

`service nginx restart`

## Final Thoughts

Once redirection is configured and functioning, ensure your C2 servers only allow ingress from the redirector and your trusted IPs (VPN, office ranges, etc).

Consider adding additional redirector protections using GeoIP restrictions (mod_maxmind) and blacklists of bad user agents and IP ranges. Thanks to [@curi0usJack](https://twitter.com/curi0usJack) for the ideas.

## References

- [Joe Vest and Andrew Chiles - cs2modrewrite.py blog post](https://posts.specterops.io/automating-apache-mod-rewrite-and-cobalt-strike-malleable-c2-profiles-d45266ca642)

- [@bluescreenofjeff - Cobalt Strike HTTP C2 Redirectors with Apache mod_rewrite](https://bluescreenofjeff.com/2016-06-28-cobalt-strike-http-c2-redirectors-with-apache-mod_rewrite/)

- [Adam Brown - Resilient Red Team HTTPS Redirection Using Nginx](https://coffeegist.com/security/resilient-red-team-https-redirection-using-nginx/)

- [Apache - Apache mod_rewrite Documentation](http://httpd.apache.org/docs/current/mod/mod_rewrite.html)