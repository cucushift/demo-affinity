# Kubernetes Affinity Demonstration
This project was developed as a response to a conversation at the December 2017
ONAP planning conference for the Beijing release of ONAP. The issue raised was
how to deploy VNFs that have specialized hardware requirements, such as
direct access to the network bits or acceleration, to compute nodes in the
ONAP cluster that support those capabilities.

It was being proposed that a "sub-system" could be built to manage this
information, which seemed redundant as Kubernetes already has this capability.
It appeared that people were unfamiliar with the capability in Kubernetes
and / or how it could be applied to the problem at hand and was suggested that
the idea be explained before the arch team or the TSC.

This code is a response to that, as "nothing explains better than working
code"(TM).

It is a fair criticism, that while Kubernetes has this capability, in ONAP today
all VNFs are VM based and thus it is immaterial if Kubernetes has this
capability.

My answer to that criticism is that while this is true, we should look at the
VIMs that control VM deployments and see if there is a similar capability and
if so leverage that when we are deploying VM based VNFs. As ONAP begins to
include container based VNFs deployed via Kubernetes we should leverage the
capabilities of Kubernetes and not invent an additional layer of abstraction.

## The Demonstration
A video demonstration of the code in this repo can be found at https://youtu.be/pQA-F4GCDQg.

## Running the demonstration
Below is are the command required to run the demonstration. There is an
assumption that you ave `vagrant` installed and it is able to create
`Ubuntu 16.04` servers and have access to the Internet.

While this demonstration creates a 3 node Kubernetes cluster it should be
possible to run the Kubernetes commands and descriptors on any Kubernetes
cluster and thus they are not constrained to run only on the demonstration
cluster.

### Create the Kubernetes Cluster
```bash
vagrant up
```

This will create 3 `Ubuntu 16.04` VMs, install `docker-ce`, and the
Kubernetes components. It will form a Kubernetes cluster with one master and
two workers. The `taint` will be removed from the master such that `pod`s can
be deployed on the master.

Additionally, the two docker images will be built on each node that are
leveraged for the demo.

- `detective:latest` - represents a hardware detection agent.
- `vnf:latest` - represents a container based VNF.

### Wait for all Nodes to be Ready

```bash
vagrant ssh k8s1
kubectl get no
```
The output of the `kubectl get no` command should be similar to

```
NAME      STATUS    ROLES     AGE       VERSION
k8s1      Ready     master    23m       v1.9.0
k8s2      Ready     <none>    8m        v1.9.0
k8s3      Ready     <none>    1m        v1.9.0
```

It may take a while for all nodes to be ready. You can periodically check the
node status using `kubectl get no` or use `watch` to periodically call the
command for you.

```bash
watch kubectl get no
```

### View Node Labels
Deployed on each node is a help script `demo-show-labels.sh`. This script uses
`kubectl get no -o json` combined with a `jq` filter to produce a listing
of the labels associated with each compute node. To view the labels simple
execute this demonstration script.

```bash
demo-show-labels.sh
```
Output:
```json
[
  {
    "name": "k8s1",
    "labels": {
      "beta.kubernetes.io/arch": "amd64",
      "beta.kubernetes.io/os": "linux",
      "kubernetes.io/hostname": "k8s1",
      "node-role.kubernetes.io/master": ""
    }
  },
  {
    "name": "k8s2",
    "labels": {
      "beta.kubernetes.io/arch": "amd64",
      "beta.kubernetes.io/os": "linux",
      "kubernetes.io/hostname": "k8s2"
    }
  },
  {
    "name": "k8s3",
    "labels": {
      "beta.kubernetes.io/arch": "amd64",
      "beta.kubernetes.io/os": "linux",
      "kubernetes.io/hostname": "k8s3"
    }
  }
]
```
Each compute node has only the standard labels assigned.

### Create Namespaces
This demonstration uses two namespaces, `onap` and `vnf`. The `onap` namespace
is used for containers that would be part of the ONAP solution, and the `vnf`
namespace is used to container managed VNFs.

There are two descriptor files to create these Namespaces.

```bash
kubectl create -f detective/onap.yml -f vnf/vnf.yml
```
Output:
```bash
namespace "onap" created
namespace "vnf" created
```

### Create Harware Detection Daemon Set
The sample docker image `detective:latest` represents a hardware detection
mechanism. The idea is that a bit of code would run on each node in the
Kubernetes cluster, interrogate the hardware on which it is running and then
add / remove labels form the node depending on the capabilities of the
hardware.

The example hardware detection agent included in this example is based on
the virus scan model, i.e. it pulls "definitions" from a remote site and then
uses those definitions to detect the hardware capabilities.

For this example it is all "fake" and a "hack" but the outcome is the
hardware detection agents will label each node differently.

To start the hardware detection `daemonset` use the following command:
```bash
kubectl create -f detective/detective.yml
```
Output:
```
daemonset "hardware-detective" created
```

### Verify Hardware Detection Daemon Set Running
Use `kubectl` to verify that there are 3 instances of the hardware detection
agent running, one on each node.
```bash
kubectl get po -n onap -o wide
```
Output:
```bash
NAME                       READY     STATUS    RESTARTS   AGE       IP          NODE
hardware-detective-bsr9m   1/1       Running   0          1m        10.44.0.1   k8s2
hardware-detective-rfzlc   1/1       Running   0          1m        10.36.0.1   k8s3
hardware-detective-x5r2z   1/1       Running   0          1m        10.32.0.3   k8s1
```

### View Node Labels (modified)
With the hardware detection agents running, they will have modified the Labels
associated with each compute node. These changes can be seen with the
`demo-show-labels.sh` script.
```bash
demo-show-labels.sh
```
Output:
```json
[
  {
    "name": "k8s1",
    "labels": {
      "beta.kubernetes.io/arch": "amd64",
      "beta.kubernetes.io/os": "linux",
      "hw.accel": "true",
      "hw.perst": "true",
      "kubernetes.io/hostname": "k8s1",
      "node-role.kubernetes.io/master": ""
    }
  },
  {
    "name": "k8s2",
    "labels": {
      "beta.kubernetes.io/arch": "amd64",
      "beta.kubernetes.io/os": "linux",
      "hw.accel": "true",
      "hw.perst": "false",
      "kubernetes.io/hostname": "k8s2"
    }
  },
  {
    "name": "k8s3",
    "labels": {
      "beta.kubernetes.io/arch": "amd64",
      "beta.kubernetes.io/os": "linux",
      "hw.accel": "false",
      "hw.perst": "false",
      "kubernetes.io/hostname": "k8s3"
    }
  }
]
```

As seen in the output above, each node has been augmented with the `hw.accel`
and `hw.perst` labels, each having a value of `true` or `false`.

_NOTE: `hw.accel` and `hw.perst` are only example labels, the actual Labels
used would be dependent on the actual implementation and the actual
capabilities available on the actual compute nodes._

### VNF Pod Files

The following Pod descriptor files will be used to deploy sample container
based VNFs:

- `vnf/must_have_accel_and_perst.yml` - deploys a VNF to a compute node that has
both acceleration and persistence
- `vnf/must_not_have_accel_and_perst.yml` - deploys a VNF to a compute node that
has neither acceleration nor persistence
- `vnf/no_preference.yml` - deploys a VNF to a compute node with no preference
about acceleration or persistence
- `vnf/must_have_accel_prefers_perst.yml.j2` - Jinja2 template used to deploy
a VNF to a compute node with acceleration and a weighted preference for
persistence

_NOTE: In the source code these files are found in the
`ansible/roles/test/files/vnf` directory._

### Deploy Initial VNFs
First the non-weighted preferenced VNFs instances will be deployed.
```bash
kubectl create -f vnf/must_have_accel_and_perst.yml \
    -f vnf/must_not_have_accel_and_perst.yml \
    -f vnf/no_preference.yml
```
Output:
```bash
pod "must-have-accel-and-perst" created
pod "must-not-have-accel-and-perst" created
pod "no-preference" created
```

### View Deployed VNFs
How Kubernetes scheduled the VNF Pods depends on their affinity settings in
their descriptor files and the labels on the compute nodes. How they were
scheduled can be seen using the `kubectl` command:
```bash
kubectl get po -n vnf -o wide
```
Output:
```bash
NAME                            READY     STATUS    RESTARTS   AGE       IP          NODE
must-have-accel-and-perst       1/1       Running   0          3m        10.32.0.4   k8s1
must-not-have-accel-and-perst   1/1       Running   0          3m        10.36.0.2   k8s3
no-preference                   1/1       Running   0          3m        10.44.0.2   k8s2
```

### Deploy VNFs with Weighted Preferences
Included in the demo is a script that will deploy a VNF that requires
acceleration (`hw.accel`), but has a weighted preference for persistence
(`hw.perst`). This script will create instances with the weights 1 through 5
and 10 to 100 at intervals of 5. The point of this is to show how kubernetes
will use weighted preferences in its scheduling algorithm.
```bash
cd vnf
demo-create-preferenced-vnfs.sh
```
Output:
```bash
pod "must-have-accel-prefers-perst-001" created
pod "must-have-accel-prefers-perst-002" created
pod "must-have-accel-prefers-perst-003" created
pod "must-have-accel-prefers-perst-004" created
pod "must-have-accel-prefers-perst-005" created
pod "must-have-accel-prefers-perst-010" created
pod "must-have-accel-prefers-perst-015" created
pod "must-have-accel-prefers-perst-020" created
pod "must-have-accel-prefers-perst-025" created
pod "must-have-accel-prefers-perst-030" created
pod "must-have-accel-prefers-perst-035" created
pod "must-have-accel-prefers-perst-040" created
pod "must-have-accel-prefers-perst-045" created
pod "must-have-accel-prefers-perst-050" created
pod "must-have-accel-prefers-perst-055" created
pod "must-have-accel-prefers-perst-060" created
pod "must-have-accel-prefers-perst-065" created
pod "must-have-accel-prefers-perst-070" created
pod "must-have-accel-prefers-perst-075" created
pod "must-have-accel-prefers-perst-080" created
pod "must-have-accel-prefers-perst-085" created
pod "must-have-accel-prefers-perst-090" created
pod "must-have-accel-prefers-perst-095" created
pod "must-have-accel-prefers-perst-100" created
```

### View Deployed VNFs
```bash
kubectl get po -n vnf -o wide
```
Output:
```bash
NAME                                READY     STATUS    RESTARTS   AGE       IP           NODE
must-have-accel-and-perst           1/1       Running   0          8m        10.32.0.4    k8s1
must-have-accel-prefers-perst-001   1/1       Running   0          1m        10.32.0.5    k8s1
must-have-accel-prefers-perst-002   1/1       Running   0          1m        10.32.0.6    k8s1
must-have-accel-prefers-perst-003   1/1       Running   0          1m        10.32.0.7    k8s1
must-have-accel-prefers-perst-004   1/1       Running   0          1m        10.32.0.8    k8s1
must-have-accel-prefers-perst-005   1/1       Running   0          1m        10.44.0.3    k8s2
must-have-accel-prefers-perst-010   1/1       Running   0          1m        10.32.0.9    k8s1
must-have-accel-prefers-perst-015   1/1       Running   0          1m        10.32.0.10   k8s1
must-have-accel-prefers-perst-020   1/1       Running   0          1m        10.32.0.11   k8s1
must-have-accel-prefers-perst-025   1/1       Running   0          1m        10.32.0.12   k8s1
must-have-accel-prefers-perst-030   1/1       Running   0          1m        10.32.0.13   k8s1
must-have-accel-prefers-perst-035   1/1       Running   0          1m        10.32.0.14   k8s1
must-have-accel-prefers-perst-040   1/1       Running   0          1m        10.32.0.15   k8s1
must-have-accel-prefers-perst-045   1/1       Running   0          1m        10.32.0.16   k8s1
must-have-accel-prefers-perst-050   1/1       Running   0          1m        10.32.0.17   k8s1
must-have-accel-prefers-perst-055   1/1       Running   0          1m        10.32.0.18   k8s1
must-have-accel-prefers-perst-060   1/1       Running   0          1m        10.32.0.19   k8s1
must-have-accel-prefers-perst-065   1/1       Running   0          1m        10.32.0.20   k8s1
must-have-accel-prefers-perst-070   1/1       Running   0          1m        10.32.0.21   k8s1
must-have-accel-prefers-perst-075   1/1       Running   0          1m        10.32.0.22   k8s1
must-have-accel-prefers-perst-080   1/1       Running   0          1m        10.32.0.23   k8s1
must-have-accel-prefers-perst-085   1/1       Running   0          58s       10.32.0.24   k8s1
must-have-accel-prefers-perst-090   1/1       Running   0          57s       10.32.0.25   k8s1
must-have-accel-prefers-perst-095   1/1       Running   0          55s       10.32.0.26   k8s1
must-have-accel-prefers-perst-100   1/1       Running   0          54s       10.32.0.27   k8s1
must-not-have-accel-and-perst       1/1       Running   0          8m        10.36.0.2    k8s3
no-preference                       1/1       Running   0          8m        10.44.0.2    k8s2
```

As seen from the above output, Kubernetes deploys the weighted preference
VNFs across the two nodes which meet the specified criteria with a preference
for `k8s1` which meets all the criteria, which `k8s2` meets only some of the
criteria.

## Cleanup
Demonstration VMs can be destroyed by existing out of the `k8s1` command shell
and then issuing a Vagrant command to destroy the VMs.
```bash
exit
vagrant destroy -f
```
