#!/usr/bin/python

from bottle import route, run, request
from bottle import static_file

DUMMY_RESPONSE = """<DOCMAP>
    <artifact Target="ALL">
        <latestSnapshotRepositoryId>foo-snapshots</latestSnapshotRepositoryId>
        <latestSnapshot>999</latestSnapshot>
    </artifact>
    <Topic Target="ALL">
        <Title>Overview</Title>
        <Topic Target="ALL">
            <Title>Basic Features</Title>
        </Topic>
        <Topic Target="ALL">
            <Title>About This Software</Title>
            <Topic Target="ALL">
                <Title>Platforms Supported</Title>
            </Topic>
        </Topic>
    </Topic>
</DOCMAP>"""


DUMMY_RESPONSE_ASSETS = """<DOCMAP>
    <artifact Target="ALL">
        <latestReleaseRepositoryId>foo-releases</latestReleaseRepositoryId>
        <version>0.14.0</version>
    </artifact>
    <artifact Target="ALL">
        <latestReleaseRepositoryId>foo-releases</latestReleaseRepositoryId>
        <version>0.17.0</version>
    </artifact>
    <Topic Target="ALL">
        <Title>Overview</Title>
        <Topic Target="ALL">
            <Title>Basic Features</Title>
        </Topic>
        <Topic Target="ALL">
            <Title>About This Software</Title>
            <Topic Target="ALL">
                <Title>Platforms Supported</Title>
            </Topic>
        </Topic>
    </Topic>
</DOCMAP>"""

assets_response="""
{"data":[
{"resourceURI":"http://example.com/service/local/repositories/hmrc-releases/content/foo/bar/foo/assets-frontend/0.14.0/",
"relativePath":"/foo/bar/foo/assets-frontend/0.14.0/","text":"0.14.0","leaf":false,"lastModified":"2014-06-09 15:36:51.0 UTC","sizeOnDisk":-1}
,{"resourceURI":"http://example.com/service/local/repositories/hmrc-releases/content/foo/bar/foo/assets-frontend/0.17.0/",
"relativePath":"/foo/bar/foo/assets-frontend/0.17.0/","text":"0.17.0","leaf":false,"lastModified":"2014-06-12 15:08:49.0 UTC","sizeOnDisk":-1}
]}
"""

@route('/ping')
def ping():
    return "pong"

@route('/service/local/lucene/search')
def xml():
    if request.query.a and "assets-frontend" == request.query.a:
        return DUMMY_RESPONSE_ASSETS
    else:
        return DUMMY_RESPONSE

@route("/service/local/repositories/foo-releases/content/foo/bar/foo/assets-frontend/")
def search_xml():
    return assets_response

@route('/content/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root="./static/")

run(host='localhost', port=8060)
