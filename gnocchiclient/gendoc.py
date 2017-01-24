# -*- encoding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import

from os_doc_tools import commands

# HACK(jd) Not sure why but Sphinx setup this multiple times, so we just avoid
# doing several times the requests by using this global variable :(
_RUN = False


def setup(app):
    global _RUN
    if _RUN:
        return
    commands.document_single_project("gnocchi", "doc/source", False)
    with open("doc/source/gnocchi.rst", "r") as f:
        data = f.read().splitlines(True)
        for index, line in enumerate(data):
            if "This chapter documents" in line:
                break
    with open("doc/source/gnocchi.rst", "w") as f:
        f.writelines(data[index+1:])
    _RUN = True
