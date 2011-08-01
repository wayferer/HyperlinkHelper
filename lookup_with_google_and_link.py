import sublime, sublime_plugin
import re, urllib, urllib2
import os, sys

cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(cmd_folder, 'chardet'))
sys.path.append(os.path.join(cmd_folder, 'pystache'))

import chardet, pystache

def clamp(xmin, x, xmax):
    if x < xmin:
        return xmin
    if x > xmax:
        return xmax
    return x;

def classify(char, charsets):
    if len(char) == 0:
        return -2

    for i in xrange(0, len(charsets)):
        if char in charsets[i]:
            return i
    return -1

class LookupWithGoogleAndLinkCommand(sublime_plugin.TextCommand):

	def get_link_with_title(self, phrase):
		try:
			url = "http://www.google.com/search?%s&btnI=I'm+Feeling+Lucky" % urllib.urlencode({'q': phrase})
			req = urllib2.Request(url, headers={'User-Agent' : "Sublime Text 2 Hyperlink Helper"}) 
			f = urllib2.urlopen(req)
			url = f.geturl()
			content = f.read()
			decoded_content = content.decode(chardet.detect(content)['encoding'])
			title = re.search(r"<title>([^<>]*)</title>", decoded_content, re.I).group(1)
			title = title.strip()
			return url, title, phrase
		except urllib2.URLError, e:
			sublime.error_message("Error fetching Google search result: %s" % str(e))
			return None

	def run(self, edit):
		nonempty_sels = []

		# set aside nonempty selections
		for s in reversed(self.view.sel()):
			if not s.empty():
				nonempty_sels.append(s)
				self.view.sel().subtract(s)

		# expand remaining (empty) selections to words
		self.view.run_command("expand_selection", {"to": "word"})

		# add nonempty selections back in
		for s in nonempty_sels:
			self.view.sel().add(s)
		
		# apply the links
		for s in reversed(self.view.sel()):
			if not s.empty():
				txt = self.view.substr(s)
				link = self.get_link_with_title(txt)
				if not link:
					continue
				self.view.replace(edit, s, pystache.render(self.view.settings().get('hyperlink_helper_link_format'), {'url': link[0], 'title?': {'title': link[1]}, 'input': link[2]}))
