# Automatically Generate Rulesets for Apache mod_rewrite or Nginx for Intelligent HTTP C2 Redirection

This project converts a Cobalt Strike profile to a functional mod_rewrite .htaccess or Nginx config file to support HTTP proxy redirection to a CobaltStrike teamserver.

You should test and tune the output as needed before depolying, but these scripts should handle the heavy lifting.

## Updates and Features

 - Rewrite Rules based on valid C2 URIs (HTTP GET, POST, and Stager) and specified User-Agent string. Result: Only requests to valid C2 URIs with a specified UA string will be proxied to the Team Server by default.
 - Uses a custom Malleable C2 profile to build a .htaccess file with corresponding mod_rewrite rules
 - Uses a custom Malleable C2 profile to build a Nginx config with corresponding proxy_pass rules
 - Supports the Cobalt Strike custom URI features as of CS 3.10
 - HTTP or HTTPS proxying to the Cobalt Strike Team Server
 - HTTP 302 Redirection to a Legitimate Site for Non-Matching Requests

## Quick start

The havex.profile example is included for a quick test.

1) Run the script against a profile
2) Save the output to .htaccess
3) Modify as needed
4) Use the script with your redirector

## Apache mod_rewrite Example

    python cs2modrewrite.py -i havex.profile -c https://TEAMSERVER -r https://GOHERE
    #### Save the following as .htaccess in the root web directory
    
    ########################################
    ## .htaccess START 
    RewriteEngine On
    ## Uncomment to enable verbose debugging in /var/logs/apache2/error.log
    # LogLevel alert rewrite:trace5
    
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

## Nginx Example

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

    a2enmod rewrite headers proxy proxy_http ssl cache
    a2dismod -f deflate
    service apache2 reload

*Note:* https://bluescreenofjeff.com/2016-06-28-cobalt-strike-http-c2-redirectors-with-apache-mod_rewrite/
"e0x70i pointed out in the comments below that if your Cobalt Strike Malleable C2 profile contains an Accept-Encoding header for gzip, your Apache install may compress that traffic by default and cause your Beacon to be unresponsive or function incorrectly. To overcome this, disable mod_deflate (via a2dismod deflate and add the No Encode ([NE]) flag to your rewrite rules. (Thank you, e0x70i!)"

### SSL support requires the following in the site config

    # Enable SSL
    SSLEngine On
    
    # Enable Proxy
    SSLProxyEngine On
    
    # Trust Self-Signed Certificates
    SSLProxyVerify none
    SSLProxyCheckPeerCN off
    SSLProxyCheckPeerName off
    SSLProxyCheckPeerExpire off

### HTACCESS
If you plan on using mod_rewrite in .htaccess files, you also need to enable the use of .htaccess files by changing `AllowOverride None` to `AllowOverride All`. For the default website, edit /etc/apache2/sites-available/default

    <Directory /var/www/>
            Options Indexes FollowSymLinks MultiViews
            AllowOverride All
            Order allow,deny
            allow from all
    </Directory>

## References

[cs2modrewrite.py blog post](https://posts.specterops.io/automating-apache-mod-rewrite-and-cobalt-strike-malleable-c2-profiles-d45266ca642)

[Apache mod_rewrite](http://httpd.apache.org/docs/current/mod/mod_rewrite.html)

[Cobalt Strike HTTP C2 Redirectors with Apache mod_rewrite](https://bluescreenofjeff.com/2016-06-28-cobalt-strike-http-c2-redirectors-with-apache-mod_rewrite/)

[Resilient Red Team HTTPS Redirection Using Nginx - Adam Brown](https://coffeegist.com/security/resilient-red-team-https-redirection-using-nginx/)
