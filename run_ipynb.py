#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
Given an IPython Notebook JSON object, run all code cells, replace
output cell with updated output and return the HTLM representation

Adapted from: https://gist.github.com/minrk/2620735
"""
import json
from queue import Empty
from bs4 import BeautifulSoup
from traitlets.config import Config
from nbconvert import HTMLExporter
from nbformat import NotebookNode
from jupyter_client import KernelManager
from pprint import pprint


def run_cell(kc, cell, timeout=60):
    #iopub.get_msgs()
    # wait for finish
    kc.allow_stdin = False
    reply = kc.execute(code=cell.source, reply=True, timeout=timeout)
    pprint(f'execute {cell.source}!')
    pprint(reply['msg_type'])
    pprint(reply['content'])

    assert not kc.allow_stdin
    outs = []
    msgs = kc.iopub_channel.get_msgs()

    for msg in msgs:
        pprint(msg['msg_type'])
        pprint(msg['content'])

    return msgs

    # while True:
    #     try:
    #
    #     except Empty:
    #         break
    #     msg_type = msg['msg_type']
    #     pprint(msg_type)
    #     if msg_type in ('status', 'pyin', 'execute_input'):
    #         #if msg_type not in ('stream', 'display_data', 'pyout'):
    #         continue
    #     elif msg_type == 'clear_output':
    #         outs = []
    #         continue
    #
    #     content = msg['content']
    #
    #     out = NotebookNode(output_type=msg_type)
    #
    #     if msg_type == 'stream':
    #         out.stream = content['name']
    #         out.text = content['text']
    #     elif msg_type in ('display_data', 'pyout'):
    #         out['metadata'] = content['metadata']
    #         for mime, data in content['data'].items():
    #             attr = mime.split('/')[-1].lower()
    #             # this gets most right, but fix svg+html, plain
    #             attr = attr.replace('+xml', '').replace('plain', 'text')
    #             setattr(out, attr, data)
    #         if msg_type == 'pyout':
    #             out.prompt_number = content['execution_count']
    #     elif msg_type == 'pyerr':
    #         out.ename = content['ename']
    #         out.evalue = content['evalue']
    #         out.traceback = content['traceback']
    #     else:
    #         print("unhandled iopub msg:", msg_type)
    #
    #     outs.append(out)
    #
    # return outs


kernelconf = '/home/jones/.local/share/jupyter/kernels/flasked-notebook/kernel.json'


def check_kernel(kc):
    shell = kc.shell_channel
    iopub = kc.iopub_channel
    heart = kc.hb_channel
    stdin = kc.stdin_channel

    print(f'checking shell alive: {shell.is_alive()}')
    print(f'checking iopub alive: {iopub.is_alive()}')
    print(f'checking heart alive: {heart.is_alive()}')
    print(f'checking stdin alive: {stdin.is_alive()}')


def start_kernel(config=kernelconf):

    kernelconfig = Config(json.loads(open(kernelconf).read()))
    km = KernelManager(config=kernelconfig)
    km.start_kernel(extra_arguments=['--pylab=inline'])
    kc = km.client()
    kc.start_channels()
    return kc


def run_notebook(nb):
    """
    Run each code cell in a given notebook and update with the new output
    """
    kernelconf = '/home/jones/.local/share/jupyter/kernels/flasked-notebook/kernel.json'
    kernelconfig = Config(json.loads(open(kernelconf).read()))
    km = KernelManager(config=kernelconfig)
    km.start_kernel(extra_arguments=['--pylab=inline'])
    try:
        kc = km.client()
        kc.start_channels()
        iopub = kc.iopub_channel
    except AttributeError:
        # IPython 0.13
        kc = km
        kc.start_channels()
        iopub = kc.sub_channel

    reply = kc.execute("pass", reply=False)
    while True:
        try:
            msg = iopub.get_msg(timeout=1)
        except Empty:
            break

    code_cells = [cell for cell in nb.cells if cell.cell_type == 'code']

    for cell in code_cells:
        try:
            cell.outputs = run_cell(kc, cell)
        except Exception as e:
            print(e)
            raise e

    kc.stop_channels()
    km.shutdown_kernel()
    del km
    return nb


def inject_params(params, nb):
    """
    Inject key/value pairs into a notebook
    """
    inject = '\n'.join([f'\n{k} = {params[k]}' for k in params])

    for cell in nb.cells:
        if cell.cell_type == 'code':
            cell.source += inject
    return nb


def convert_nb_html(nb):
    """
    Convert a notebooks output to HTML
    """
    nb = run_notebook(nb)
    config = Config({'HTMLExporter': {'default_template': 'basic'}})
    exportHtml = HTMLExporter(config=config)
    html, resources = exportHtml.from_notebook_node(nb)
    soup = BeautifulSoup(html)
    filters = ["output", "text_cell_render border-box-sizing rendered_html"]
    return ''.join(map(str, soup.findAll("div", {"class": filters})))
