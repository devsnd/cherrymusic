#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd -P)"
REPO_PATH="$( dirname $DIR)"
FIXTURES_DIR="cherrymusic/fixtures"

MODELS="core.Playlist core.Track core.User core.UserSettings core.HotkeysSettings core.MiscSettings storage.File storage.Directory"

cd $REPO_PATH
mkdir web/$FIXTURES_DIR

for MODEL in $MODELS
do
    MODEL_UNDERSCORE_CASE="$( echo $MODEL | cut -d '.' -f 2 | sed -e 's/^./\L&\E/' | sed 's/\([a-z0-9]\)\([A-Z]\)/\1_\L\2/g' )"
    docker-compose -f development.yml run --rm web_dev            \
        python3 manage.py dumpdata --indent 4                     \
        --output $FIXTURES_DIR/$MODEL_UNDERSCORE_CASE.json $MODEL

done