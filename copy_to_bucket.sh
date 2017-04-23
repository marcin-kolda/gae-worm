#!/usr/bin/env bash
VERSION=v1
find . -name "*.pyc" -type f -delete
zip -r gae-worm-${VERSION}.zip * -x *.iml

gsutil cp gae-worm-${VERSION}.zip gs://gae-worm
gsutil acl ch -u AllUsers:R gs://gae-worm/gae-worm-${VERSION}.zip
gsutil setmeta -h "Cache-Control:private, max-age=0, no-transform" gs://gae-worm/gae-worm-${VERSION}.zip
rm gae-worm-${VERSION}.zip
