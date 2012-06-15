# settings for python_example

VERSION_TAG_SETTINGS = { # commented lines are defaults
#    'link_root': 'site_media', # path snippet to media in url (no slashes).
#    'file_root': 'media', # relative path to media (no leading or trailing slash)
#    'debug': True, # Should probably keep True, prints out what it is changing.
    'blacklist': ['media/build'], # A list of substrings of source files+paths you don't want updated
    'trigger_file_sets': [ # a list of tuples where the left being in the name of a file that changed     triggers the right to be added to the list of files to update the version tags on.
        # We use this to combine all css/js into individual scripts at a later step in the process.
        ('.js', 'media/build/site.js'), # If a js file is changed, also update media/build/site.js
        ('.css', 'media/build/style.css'), # If a css file is changed, also update media/build/style.css
    ],
#    'extensions': ['css', 'js', 'png', 'jpg', 'jpeg', 'gif'],
#    'auto_commit_to_git': True,
#    'commit_message': '[master] Update version tags.',
}
