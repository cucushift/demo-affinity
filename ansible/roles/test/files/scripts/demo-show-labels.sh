#!/bin/bash
kubectl get no -o json | jq -C '[ .items[] | { "name": .metadata.name, "labels": .metadata.labels } ]'
