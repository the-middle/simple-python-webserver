# Simple python http server

This app only responds to this types of paths:

    http://example.local/?5=x
    http://example.local/blacklisted

## How to deploy to minikube

- install [Docker](https://docs.docker.com/engine/install/)
- Install [kubectl](https://kubernetes.io/ru/docs/tasks/tools/install-kubectl/)
- Install [Helm](https://helm.sh/docs/intro/install/)
- Install [QEMU](https://minikube.sigs.k8s.io/docs/drivers/kvm2/) to use kvm2 as driver for Minikube
- Install [Minikube](https://kubernetes.io/ru/docs/tasks/tools/install-minikube/)
- Start minikube with cni installed to be able to use Network Policies: `minikube start --vm-driver=kvm2 --network-plugin=cni --cni=calico`
- Clone the repo `link`
- Deploy PostgreSQL to minikube: `helm upgrade --install postgresql ./postgresql/`

> Remember! You can change username and password and all other things in the values.yaml file.

- Build image: `docker build -t simple-app:v1.0 .`
- Upload image to minikube: `minikube image load simple-app:v1.0`
- Change values in the `/app/values.yaml` and in `/app/secrets.yaml`.

> Tested with Gmail. To use with Gmail you need to create application password in you Google Account and provide it to the app.

- Deploy helm chart to the minikube: `helm upgrade --install simple-app ./app/`.

> You can do it in one line: `docker build -t simple-app:v1.0 . && minikube image load simple-app:v1.0 && helm upgrade --install simple-app ./app/`

- Open another terminal session and open tunnel to use `LoadBalancer` service localy: `minikube tunnel` and type in your sudo password.
- Wait a minute for it to work and find an [External Ip](https://minikube.sigs.k8s.io/docs/handbook/accessing/) of a service: `kubectl get svc`.
- Add this External ip to your hosts file: `sudo echo "[Your external ip] example.local" >> /etc/hosts`

## How it works

- App responds to the `http://host/?n=x` and returns n*n.
- App responds to the `http://host/blacklisted` and returns 444 error, while blocking your IP from accessing Pod with deploying network pilicy to the cluster and logging your: url path, ip and datetime of blocking to PostgreSQL and sends you an email with ip address of the intruder.
