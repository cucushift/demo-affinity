#!/bin/bash

for i in $(seq 1 4 | xargs printf "%03d "); do
    cat must_have_accel_prefers_perst.yml.j2 | docker run -e WEIGHT=$i -i opencord/voltha-j2 - | kubectl create -f -
done

for i in $(seq 5 5 100 | xargs printf "%03d "); do
    cat must_have_accel_prefers_perst.yml.j2 | docker run -e WEIGHT=$i -i opencord/voltha-j2 - | kubectl create -f -
done
