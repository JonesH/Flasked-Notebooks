#!/usr/bin/env python
#! -*- coding: utf-8 -*-

import os
import forms
import nbformat

from glob import glob
from os.path import basename
from run_ipynb import convert_nb_html, inject_params
from flask import Flask, request, render_template, abort, g

app = Flask(__name__)
app.secret_key = os.urandom(128)


@app.before_request
def before_request():
    g.nbs = [basename(f).split('.')[0] for f in glob('notebooks/*ipynb')]


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/notebook/adder.ipynb", methods=['GET', 'POST'])
def adder():
    """
    Inject input parameters to the adder notebook before rendering
    """
    if request.method == 'POST':
        notebook = nbformat.read('notebooks/adder.ipynb', 4)  # nbformat.NO_CONVERT)
        notebook = inject_params(request.form, notebook)
        html_notebook = convert_nb_html(notebook)
        return render_template('notebook.html', content=html_notebook)
    else:
        params = forms.AdderForm()
        return render_template('adder.html', form=params)


@app.route("/notebook/<notebook>")
def notebook(notebook):
    """
    Dynamically render IPython Notebook
    """
    try:
        notebook = nbformat.read(f'notebooks/{notebook}', 4)  # nbformat.NO_CONVERT)
    except IOError:
        abort(418)
    html_notebook = convert_nb_html(notebook)
    return render_template('notebook.html', content=html_notebook)


#if __name__ == "__main__":
#    app.run(debug=True)
