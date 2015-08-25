#!/usr/bin/python

from bottle import route, run, request
from bottle import static_file

MAVEN_METADATA="""<?xml version="1.0" encoding="UTF-8"?>
<metadata>
  <groupId>uk.gov.hmrc</groupId>
  <artifactId>help-frontend_2.11</artifactId>
  <version>1.26.0-3-gd7ed03c</version>
  <versioning>
    <latest>1.26.0-3-gd7ed03c</latest>
    <release>1.26.0-3-gd7ed03c</release>
    <versions>
      <version>1.26.0-1-gd0dba7c</version>
      <version>1.26.0-2-gd213a4f</version>
      <version>1.26.0-3-gd7ed03c</version>
    </versions>
    <lastUpdated>20150804143826</lastUpdated>
  </versioning>
</metadata>"""


@route('/ping')
def ping():
    return "pong"

@route('/hmrc/release-candidates/uk/gov/hmrc/playtest_2.11/maven-metadata.xml')
def maven_metadata():
    return MAVEN_METADATA

@route('/hmrc/release-candidates/uk/gov/hmrc/playtest_2.11/1.26.0-3-gd7ed03c/playtest_2.11-1.26.0-3-gd7ed03c.tgz')
def server_static_tgz():
    return static_file("bintray/playtest.tgz", root="./static/")

@route('/hmrc/release-candidates/uk/gov/hmrc/playtest_2.11/1.26.0-3-gd7ed03c/playtest_2.11-1.26.0-3-gd7ed03c.tgz.md5')
def server_static_md5():
    return static_file("bintray/playtest.tgz.md5", root="./static/")

run(host='localhost', port=8061)
