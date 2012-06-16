#!/usr/bin/env python
try:
    from django.conf import settings
    settings.INSTALLED_APPS # Here to force it to fail if this isn't a real django project.
    from django.core.management.base import BaseCommand
    django_version = True
except:
    import settings
    django_version = False

import subprocess, re, string, random

class VersionUpdater():
    def __init__(self, start_commit='', end_commit=''):
        self._try_settings('link_root', 'site_media')
        self._try_settings('file_root', 'media')
        self._try_settings('debug', True)
        self._try_settings('blacklist', [])
        self._try_settings('trigger_file_sets', [])
        self._try_settings('extensions', ['css', 'js', 'png', 'jpg', 'jpeg', 'gif'])
        self._try_settings('auto_commit_to_git', True)
        self._try_settings('commit_message', '[master] Update version tags.')

        self.start_commit = start_commit
        self.end_commit = end_commit
        self.changed_files = []
        self.files_handled = []
        self.something_updated = False

        git_status = self._shell_to_str('git status')
        if 'On branch master' not in git_status:  self._error_exit( "Alert! Not in master, can't update version tags!" )
        if 'nothing to commit' not in git_status: self._error_exit( "Alert! Uncommitted Changes, can't update version tags!" )
        if self._shell_to_str('git diff origin/master') != '': self._error_exit( "Alert! Local master not in sync with origin/master!" )

    def _try_settings(self, name, default):
        setattr(self, name, settings.VERSION_TAG_SETTINGS.get(name, default))

    def update_versions(self):
        if self.debug: print 'Updating version tags'
        if not self.start_commit: self._set_commits()
        self._get_updated_files()
        while len(self.changed_files) > 0:
            f = self.changed_files.pop()
            self._update_references_to_file(f)
        if self.something_updated:
            if self.auto_commit_to_git:
                self._shell_to_str('git commit -am "' + self.commit_message + '"')
                self._shell_to_str('git push origin master')
                if self.debug: print 'Updates commited and pushed to git.'
            else:
                if self.debug: print 'Updates made but not yet commited to git.'
        else:
            if self.debug: print 'No files reference changed files.'

    def _list_has_substring(self, l, s):
        for ss in l:
            if ss in s: return True
        return False

    def _get_updated_files(self):
        c = 'git diff --name-only ' + self.start_commit + ' ' + self.end_commit + '|grep "^'+self.file_root+'/"|grep -e "\.' + \
                '$" -e "\.'.join(self.extensions) + '$"'

        for f in self._shell_to_str(c).strip().split('\n'):
            if not f or self._list_has_substring(self.blacklist, f):continue
            self.changed_files.append(f)

        if not self.changed_files:
            if self.debug: print 'Nothing to update'
            exit(0)

    def _update_references_to_file(self, f):
        if self.debug: print '-------', f, '-------'
        stripped = f.lstrip(self.file_root)
        files_with_reference = []
        for line in self._shell_to_str('grep -R "'+stripped+'" ./ --exclude-dir=".git" --exclude="*.pyc" | grep '+self.link_root).strip().split('\n'):
            if not line: continue
            vtag = ''
            if 'version-' in line:
                try:
                    vtag = line.split('version-')[1].split('/')[0]
                except: pass
            f_tuple = (line.lstrip('./').split(':')[0], vtag)
            if f_tuple not in files_with_reference:
                files_with_reference.append(f_tuple)

        self._update_vtags_in_files(stripped, files_with_reference)
        self.files_handled.append(f)
        for substring, triggered in self.trigger_file_sets:
            if substring in f and triggered not in self.changed_files and triggered not in self.files_handled:
                self.changed_files.append(triggered)
        self._queue_chained_updates(files_with_reference)

    def generate_vtag(self):
        return ''.join(random.choice(string.ascii_letters+string.digits) for i in range(10))

    def _update_vtags_in_files(self, include_name, files_with_reference):
        vtag = self.generate_vtag()
        if self.debug: print "Updating references to", include_name, 'to version', vtag, 'in the following files'
        for f, old_vtag in files_with_reference:
            if self.debug: print '\t', f
            if old_vtag != '':
                self._shell_to_str('sed -i "s#'+self.link_root+'/version-'+old_vtag+'/'+include_name+'#'+self.link_root+'/version-'+vtag+'/'+include_name+'#" ' + f)
            else:
                self._shell_to_str('sed -i "s#'+self.link_root+'/'+include_name+'#'+self.link_root+'/version-'+vtag+'/'+include_name+'#" ' + f)
            self.something_updated = True

        if self.debug: print

    def _queue_chained_updates(self, files):
        for f, n in files:
            try:
                ext = f.rsplit('.', 1)[1]
            except: continue
            if ext in self.extensions \
                    and re.match(self.file_root, f) \
                    and f not in self.changed_files \
                    and f not in self.files_handled:
                self.changed_files.append(f)

    def _set_commits(self):
        i = 2
        start_commit = self._shell_to_str("git log | sed -n 1p | sed 's/[^a-zA-Z0-9]//g'").strip()
        start_commit = re.match(r'[3m]*commit(.{40})m?', start_commit).group(1)
        self.end_commit = start_commit
        line = line_stripped = start_commit
        stripped_commit_message = re.sub(r'[^0-9a-zA-Z]', '', self.commit_message)
        while line and line_stripped != stripped_commit_message:
            line = self._shell_to_str("git log | sed -n " +str(i)+ "p | sed 's/[^a-zA-Z0-9]//g'")
            line_stripped = line.strip()
            if 'commit' in line_stripped and len(line_stripped) in [56, 50]:
                start_commit = re.match(r'[3m]*commit(.{40})m?', line_stripped).group(1)
            i += 1
        self.start_commit = start_commit

    def _error_exit(self, error_message):
        print error_message
        exit(1)

    def _shell_to_str(self, c):
        return subprocess.Popen([c], stdout=subprocess.PIPE, shell=True).stdout.read()

if django_version:
    class Command(BaseCommand):
        args = 'none'
        help = 'Updates references to media files so that CDN will always request the right version.'

        def handle(self, *args, **options):
            vu = VersionUpdater()
            vu.update_versions()

elif __name__ == "__main__":
    vu = VersionUpdater()
    vu.update_versions()
