version-tags
============

Django command/Python script that allows you to easily update the paths in references/links to static media that has changed according to your git history. This allows you to use any CDN/cache you want without worrying about someone returning to your site and getting new html that doesn't work with old js/css/images.

# Requirements
* __A server that allows you to set up wildcard aliases.__ The following all work:
  * apache
  * nginx
  * django's dev server (runserver)
* __A git repository__ (Changes are tracked by checking what files have changed since the last time you ran the script)
* Unix-like system with the following tools:
  * sed
  * grep
  * git
* Track your code in git and be able to push to master (pushing is optional, but recommended)
  * This script __REQUIRES__ that you are in the master branch of your project. This is prevent version tags from getting skipped if you merge in a branch that had version tags run on it after a branch that didn't making it so the files changed since the last version tags update commit don't include all of the files changed and not yet updated.
  * This script also __REQUIRES__ that all previous changes are committed to master (your working directory needs to be clean and up to date with origin/master).

# Introduction

version-tags is used to allow you to completely ignore caches (Server/CDN/browser caching) by giving each changed file a completely new path.

## Example: 

If you change a media file media/js/site.js that is served from http://example.com/site_media/js/site.js this script will rewrite the links in any files that reference site_media/js/site.js to something like site_media/version-xk91FYpxFt/js/site.js.

If you were to make another change to the file before rerunning the script it would change yet again to: site_media/version-lS8fCOWUbU/js/site.js

# Usage

## Django

Put the update_version_tags.py file in an app that is "INSTALLED" in your django project with the directory structure: management/commands/update_version_tags.py

Example:

If you create an app "utils" (Don't forget to add "utils" to INSTALLED_APPS in settings.py) your structure would be:
```
settings.py
...
utils/
  __init__.py
  management/
    __init__.py
    commands/
      __init__.py
      update_version_tags.py
```

You should then modify the settings in settings.py to suit your needs (See the Configuration section).

When you have the settings tuned, you can run the script with:

    python manage.py update_version_tags
  
## Python

Put the update_version_tags.py script in the root of your project.

You should then create a settings.py file and set settings to suit your needs (See the Configuration section).

When you have the settings tuned, you can run the script with:

    ./update_version_tags.py

# Configuration

Both methods (Python and Django (same script can be used either way)) import settings.py from the root directory of your project to get a VERSION_TAG_SETTINGS dict, though the Django version imports using the `from django.conf import settings` method.

## Settings

See python_example/settings.py or django_example/settings.py for examples of an actual dict.

### link_root

default: `"site_media"`

This should be something non-common to prevent false-positives since it is used to filter what lines of code need to be updated.

### file_root

default: `"media"`

This is the path to the media directory __relative to the git repository root__ without leading or trailing slashes.

### debug

default: `True`

If True it will tell you useful things such as which files are changing or if no files were changed. Errors will always be printed to the screen.

### blacklist

default: `[]`

This is a list of partial filenames/paths you don't want the version tags script to track (note: this doesn't effect trigger_file_sets)

### trigger_file_sets

default: `[]`

This ignores the blacklist and is a list of tuples of a file to change if another file that has changed matches a certain string and hasn't been added before.

Example:

`[('.js', 'media/build/site.js')]` will update the version tags for references to media/build/site.js even if 'media/build' is in the blacklist.

### extensions

default: `['css', 'js', 'png', 'jpg', 'jpeg', 'gif']`

All of the file extensions you want to be handeled by version tags (the . is automatically added to the beginning and so is a trailing $ for regex style matching to prevent false positives).

### auto_commit_to_git

default: `True`

If True it will create a new commit using the commit message below AND push to origin master

### commit_message

default: `'[master] Update version tags.'`

This is used for not just creating the git commit but __ALSO__ to determine where to start the `git diff --name-only` from.

__IMPORTANT:__ If you ever change this, or if you don't auto-commit and commit manually with a different commit message this script will not know where to start from and will iterate through your entire git log until the earliest commit and diff from there.

This happens because the git diff starts from the first time the script finds the `commit_message` it is expecting until the most recent commit.

If you don't want to use this and want to specify a start and end commit you can import the VersionUpdater class and init it with start_commit and end_commit or modify them before calling update_versions()

# Configuring Servers

## Django dev server

See the django_example/urls.py file (in the `if settings.DEBUG:` block).

Note: You'll need to set a STATIC_URL_REL that would be "site_media/" if your STATIC_URL="http://example.com/site_media/" (see settings.py)

## Nginx server

Add the following lines to your /etc/nginx/sites-enabled/<config_file> in a `server {}` block:

    location /site_media {
        rewrite "/site_media/version-[^/]+/(.*)" /site_media/$1;
        alias   /var/media/;
        expires 30d;
        add_header Cache-Control public;
    }

Make sure /site_media/ and /var/media/ are correct for your install.

## Apache

Add the following line to your /etc/apache/sites-enabled/<config_file> in the `<VirtualHost>` block.

    AliasMatch ^/site_media/(version-[^/]*/)?(.*) /var/media/$2

Make sure /site_media/ and /var/media/ are correct for your install and that you have mod_alias enabled.

# History

This started about 2 years ago when we got fed up with manually changing get variables on each link to our css/js files from `?v=1.1` to `?v=1.2` when we made a change to them.

The first version of the script was a very crude bash script that printed out exactly what it was doing because sometimes it had to be corrected.

About a year ago, we started using Amazon Cloudfront as a CDN for our front end media which was great. The issue is they ignore get variables so our version tags no longer worked at all. I decided that the easiest solution was to update the media path in links, and reconfigure our server to serve the file with a wildcard in the path.

This week, while configuring jenkins-ci to automate build/testing for our newest project I decided to port the script from bash to python (though not ditching grep and sed) in order to more easily add the necessary functionality of chaining updated files (which before had been done by hand when I noticed that an image was update which was referenced in a css file which meant the css file would need new version tags as well.)

I also changed it from /version-number/ (`/version-2/`) to /version-random_string/ (`/version-iND09jxvP7/`) in order to prevent someone from manually requesting `/version-3/` when the references are still `/version-2/` which would populate Caches/CDNs for a future URL with a copy of the current version of the file. If you decide this isn't the functionality you want, you can rewrite the generate_vtag function (you will also need to use the old_vtag variables to find the max(old_vtag) to increment from (if somehow the vtags get out of sync you'll want to increment past the largest vtag otherwise it's possible the old version has already been cached in the CDN from a different reference)).

# Bug reports/support

Feel free to use the issue tracker, email sam@ our company's url or look up sssbox on github.
