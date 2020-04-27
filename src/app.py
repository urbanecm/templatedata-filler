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

import os
import yaml
import re
from flask import redirect, request, jsonify, render_template, url_for, \
    make_response, flash
from flask import Flask
import requests
from flask_jsonlocale import Locales
from flask_mwoauth import MWOAuth
from SPARQLWrapper import SPARQLWrapper, JSON
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from mediawiki import MediaWiki
from template import Template

app = Flask(__name__, static_folder='../static')

# Load configuration from YAML file
__dir__ = os.path.dirname(__file__)
app.config.update(
    yaml.safe_load(open(os.path.join(__dir__, os.environ.get(
        'FLASK_CONFIG_FILE', 'config.yaml')))))
locales = Locales(app)
_ = locales.get_message

db = SQLAlchemy(app)
migrate = Migrate(app, db)

mwoauth = MWOAuth(
    consumer_key=app.config.get('CONSUMER_KEY'),
    consumer_secret=app.config.get('CONSUMER_SECRET'),
    base_url=app.config.get('OAUTH_MWURI'),
    return_json=True
)
app.register_blueprint(mwoauth.bp)

def logged():
    return mwoauth.get_current_user() is not None

@app.before_request
def force_login():
    if not logged() and '/login' not in request.url and '/oauth-callback' not in request.url:
        return render_template('login.html')

@app.context_processor
def inject_base_variables():
    return {
        "logged": logged(),
        "username": mwoauth.get_current_user()
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.args.get('template') is None or request.args.get('wiki') is None:
        return render_template('choose_template.html')
    
    tmpl = Template(request.args.get('template'), MediaWiki(request.args.get('wiki'), mwoauth))
    params = tmpl.get_missing_params()

    if request.method == 'POST':
        new_params = {}
        for key_raw in request.form:
            key = key_raw.split('-')
            param = key[0]
            type = key[1]
            value = request.form[key_raw]

            if value == "":
                continue

            if param not in new_params:
                new_params[param] = {
                    "required": False,
                    "label": param
                }

            if type == "label":
                new_params[param]["label"] = value
            elif type == "description":
                new_params[param]["description"] = value
            elif type == "required":
                new_params[param]["required"] = True

        tmpl.patch_templatedata_params(new_params)
        flash('TemplateData were updated')

    return render_template('tool.html', params=params, wiki=request.args.get('wiki'), template=request.args.get('template'))

@app.route('/api/<path:wiki>/<path:template>.json')
def api_template(wiki, template):
    tmpl = Template(template, MediaWiki(wiki, mwoauth))
    return jsonify({
        "wiki": wiki,
        "template": template,
        "params_done": tmpl.params_done,
        "params_all": tmpl.params_all
    })


@app.route('/test.json')
def test():
    tmpl = Template("Šablona:Infobox - film", MediaWiki("cs.wikipedia.org", mwoauth))
    return jsonify(tmpl.get_missing_params())
    return tmpl.patch_templatedata_params({
        "jazyk": {
            "required": False,
            "label": "Jazyk",
            "description": "Jazyk, ve kterém je film natočen"
        }
    })

if __name__ == "__main__":
    app.run()