#!/bin/bash

kubectl delete -n vnf $(kubectl get po -n vnf -o name)
