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

import re
import simplejson as json

class Template():
    page_title = None
    mw = None
    mTemplatedata = None
    mText = None
    mTemplatedataStorage = None
    mTemplatedataStorageContent = None

    def __init__(self, page_title, mw):
        self.page_title = page_title
        self.mw = mw
    
    @property
    def templatedata(self):
        if self.mTemplatedata:
            return self.mTemplatedata
        r = self.mw.request({
            "action": "templatedata",
            "format": "json",
            "titles": self.page_title
        }).get('pages', {})
        self.mTemplatedata = r[list(r.keys())[0]]
        return self.mTemplatedata
    
    @property
    def text(self):
        if self.mText:
            return self.mText
        self.mText = self.mw.get_content(self.page_title)
        return self.mText
    

    @property
    def params_done(self):
        return len(self.get_td_params())
    
    @property
    def params_all(self):
        return len(self.get_all_params())
    
    def get_templatedata_storage(self):
        if self.mTemplatedataStorage:
            return self.mTemplatedataStorage

        TAG = '<templatedata>'
        if TAG in self.text:
            self.mTemplatedataStorage = self.page_title
        elif TAG in self.mw.get_content("%s/doc" % self.page_title, ignore_missing=True):
            self.mTemplatedataStorage = "%s/doc" % self.page_title
        return self.mTemplatedataStorage
    
    def get_templatedata_storage_content(self):
        if self.mTemplatedataStorageContent:
            return self.mTemplatedataStorageContent
        self.mTemplatedataStorageContent = self.mw.get_content(self.get_templatedata_storage())
        return self.mTemplatedataStorageContent

    def get_all_params(self):
        params = self.text.replace('{{{', '\n{{{')
        params = re.sub(r'(?m)^((?!\{\{\{).)*$', r'', params)
        params = re.sub(r'[<|}][^\n]*', r'', params)
        params = params.replace('{{{', ' | ')
        params = list(filter(None, params.split('\n')))
        params = list(map(lambda x: x.replace('|', '').strip(), params))
        return set(params)
    
    def get_td_params(self):
        return self.templatedata.get('params')
    
    def get_missing_params(self):
        return list(filter(lambda x: x not in self.get_td_params(), self.get_all_params()))
    
    def get_raw_templatedata(self):
        return json.loads(re.search(r'<templatedata>(.*)</templatedata>', self.get_templatedata_storage_content(), re.DOTALL).group(1))

    def patch_templatedata_params(self, params):
        raw_templatedata = self.get_raw_templatedata()
        raw_templatedata.get('params').update(params)
        text = self.get_templatedata_storage_content()
        text = re.sub(
            r'<templatedata>.*</templatedata>',
            '<templatedata>\n%s\n</templatedata>' % json.dumps(raw_templatedata, indent=4),
            text,
            flags=re.DOTALL
        )
        return self.mw.put_content(self.get_templatedata_storage(), text, "Přidání parametrů do TemplateDat")