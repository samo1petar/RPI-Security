#!/bin/bash

SRC_DIR="/home/rpiz1/RPI-Security/images"
DEST_DIR="/home/alfred/Projects/Security_Cameras/Data/images/rpiz1"
LOCAL_USER="alfred"
LOCAL_IP="alfred.local"

while true; do
  inotifywait -e modify,create,delete,move "$SRC_DIR"
  rsync --remove-source-files -aP $SRC_DIR $LOCAL_USER@$LOCAL_IP:$DEST_DIR/
done
