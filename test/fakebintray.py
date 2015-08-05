#!/usr/bin/python

from bottle import route, run, request
from bottle import static_file

LATEST_VERSION_RESPONSE="""
{"name":"1.26.0-3-gd7ed03c","desc":null,"package":"playtest","repo":"release-candidates","owner":"hmrc","labels":[],"attribute_names":[],"created":"2015-08-04T14:35:27.173Z","updated":"2015-08-04T14:38:26.150Z","released":"2015-08-04T14:35:38.862Z","ordinal":3.0,"github_release_notes_file":null,"github_use_tag_release_notes":false,"vcs_tag":null}
"""

VERSION_FILES_RESPONSE="""
[
{"name":"playtest_2.11-1.26.0-3-gd7ed03c-javadoc.jar",
"path":"uk/gov/hmrc/playtest_2.11/1.26.0-3-gd7ed03c/playtest_2.11-1.26.0-3-gd7ed03c-javadoc.jar",
"repo":"release-candidates",
"package":"playtest","version":"1.26.0-3-gd7ed03c",
"owner":"hmrc",
"created":"2015-08-04T14:35:30.567Z",
"size":489312,
"sha1":"1c058c5e516f76ce5beb90931d3db00114560991"
},{
"name":"playtest_2.11-1.26.0-3-gd7ed03c.tgz",
"path":"uk/gov/hmrc/playtest_2.11/1.26.0-3-gd7ed03c/playtest_2.11-1.26.0-3-gd7ed03c.tgz",
"repo":"release-candidates",
"package":"playtest",
"version":"1.26.0-3-gd7ed03c",
"owner":"hmrc",
"created":"2015-08-04T14:36:47.013Z",
"size":32643270,
"sha1":"5c6d23596ba70e47fc5623275853676fc4a521ef"
},{
"name":"playtest_2.11-1.26.0-3-gd7ed03c.tgz.md5",
"path":"uk/gov/hmrc/playtest_2.11/1.26.0-3-gd7ed03c/playtest_2.11-1.26.0-3-gd7ed03c.tgz.md5",
"repo":"release-candidates",
"package":"playtest",
"version":"1.26.0-3-gd7ed03c",
"owner":"hmrc",
"created":"2015-08-04T14:36:47.013Z",
"size":32643270,
"sha1":"5c6d23596ba70e47fc5623275853676fc4a521ef"
}]
"""

@route('/ping')
def ping():
    return "pong"

@route('/packages/hmrc/release-candidates/playtest/versions/_latest')
def latest_version():
    return LATEST_VERSION_RESPONSE

@route("/packages/hmrc/release-candidates/playtest/versions/1.26.0-3-gd7ed03c/files")
def version_files():
    return VERSION_FILES_RESPONSE

@route("/packages/hmrc/release-candidates/playtest/versions/1.26.0-3-gd7ed03c/files")
def version_files():
    return VERSION_FILES_RESPONSE

@route('/hmrc/release-candidates/uk/gov/hmrc/playtest_2.11/1.26.0-3-gd7ed03c/playtest_2.11-1.26.0-3-gd7ed03c.tgz')
def server_static_tgz():
    return static_file("bintray/playtest.tgz", root="./static/")

@route('/hmrc/release-candidates/uk/gov/hmrc/playtest_2.11/1.26.0-3-gd7ed03c/playtest_2.11-1.26.0-3-gd7ed03c.tgz.md5')
def server_static_md5():
    return static_file("bintray/playtest.tgz.md5", root="./static/")

run(host='localhost', port=8061)
