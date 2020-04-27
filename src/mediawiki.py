# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

class MediaWiki():
    mwoauth = None
    root_url = None

    def __init__(self, wiki_domain, mwoauth):
        self.root_url = "https://%s/w" % wiki_domain
        self.mwoauth = mwoauth
    
    def request(self, payload):
        return self.mwoauth.request(payload, self.root_url)
    
    def get_token(self, type="csrf"):
        return self.request({
            "action": "query",
            "format": "json",
            "meta": "tokens",
            "type": type
        })["query"]["tokens"]["%stoken" % type]

    def get_content(self, page_title, rvslot="main", ignore_missing=False):
        payload = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": page_title,
            "rvprop": "content",
            "rvslots": rvslot
        }
        data = self.request(payload)["query"]["pages"]
        if "revisions" not in data[list(data.keys())[0]]:
            if ignore_missing:
                return ""
            raise ValueError("The requested content doesn't exist")

        return data[list(data.keys())[0]]["revisions"][0]["slots"][rvslot]["*"]
    
    def put_content(self, page_title, text, summary, minor=False):
        return self.request({
            "action": "edit",
            "format": "json",
            "title": page_title,
            "text": text,
            "summary": summary,
            "token": self.get_token(),
            "minor": minor
        })