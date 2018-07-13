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

@route('/ping')
def ping():
    return "pong"

@route('/service/local/lucene/search')
def xml():
        return DUMMY_RESPONSE

@route('/content/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root="./static/")

run(host='localhost', port=8060)
