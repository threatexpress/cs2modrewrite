# Convert Cobalt Strike profiles to Apache mod_rewrite .htaccess files to support HTTP C2 Redirection

This is a quick script that converts a Cobalt Strike profile to a base mod_rewrite .htaccess file to support HTTP redirection with Cobalt Strike

You will most likely want to tune and test before use, but it does help get the script started.

This was heavily based on the work by Jeff Dimmock @bluescreenofjeff

## Quick start

The havex.profile example is included for a quick test.

1) Run the script against a profile
2) Save the output to .htaccess
3) Modify as needed
4) Use script with your Apache redirector

## Example

    python csToModrewrite.py -i havex.profile -c http://myteamserver.com -d http://google.com
    
    RewriteEngine On
    RewriteCond %{REQUEST_URI} ^/(/include/template/isx.php|/wp06/wp-includes/po.php|/wp08/wp-includes/dtcla.php|/modules/mod_search.php|/blog/wp-includes/pomo/src.php|/includes/phpmailer/class.pop3.php)/?$
    RewriteCond %{HTTP_USER_AGENT} ^Mozilla/5\.0\ (Windows;\ U;\ MSIE\ 7\.0;\ Windows\ NT\ 5\.2)\ Java/1\.5\.0_08)?$
    RewriteRule ^.*$ http://myteamserver.com{REQUEST_URI} [P]
    RewriteRule ^.*$ http://google.com/? [L,R=302]

## References

Refer to the bluescreenofjeff blog post for more details

[Cobalt Strike HTTP C2 Redirectors with Apache mod_rewrite](https://bluescreenofjeff.com/2016-06-28-cobalt-strike-http-c2-redirectors-with-apache-mod_rewrite/)