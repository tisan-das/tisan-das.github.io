---
layout: post
title: Scaling on Queued Messages
published: true
---

Queue-based systems are one of the most prominent ways of propagating events and notifications. Due to the widespread usage, the majority of the cloud service providers also have offerings of enterprise-grade queueing mechanisms. Apart from that many organizations also have their internally hosted queue applications like Kafka, and ActiveMQ, which multiple services utilize. The primary concern from the perspective of designing distributed systems with a queueing mechanism is when there's a requirement to absorb the burst of messages without delay. The worker nodes processing the messages are needed to scaled without delay.


SQS provides support for ```ApproximateNumberOfMessages``` attribute, which keeps track of the messages present in the queue. A custom metric can be used to scale the worker nodes based on this. However, it's to be noted that in case an AWS CloudWatch metric is created out of this parameter, then the CloudWatch metric is generally updated in 5 minutes, and hence relying upon the CloudWatch metric might not provide real-time data. Hence it's better to have an autoscaler designed that would continuously poll for this attribute, and scale the worker nodes depending upon certain heuristics.

Now, even though scale-up can be done with simple heuristics, when the number of messages keeps increasing the worker nodes are to need to be scaled up. However, the scale-down operations are not so straightforward. For example, in the case of an optimal configuration, the incoming messages are consumed immediately, hence the value of the attribute ```ApproximateNumberOfMessages``` would be 0. So essentially, scale-down is needed when the worker nodes are idle, and the incoming messages are also getting consumed without delay.

Kubernetes provides support for horizontal pod autoscaling, where the autoscaler sits on the control plane, continues to monitor the metric specified, and follows the scaling algorithm based on the metrics data captured. Practo provides an open-source SQS and Beanstalkd autoscaler called Worker Pod Autoscaler. This WPA can be used to actively scale the worker nodes.


### Hands-on with Worker Pod Autoscaler to scale SQS:

###### Step 01: Export the environment variables related to IAM: 
```sh
export AWS_REGION='ap-south-1,ap-southeast-1'
export AWS_ACCESS_KEY_ID='<access_key_id>'
export AWS_SECRET_ACCESS_KEY='<secret_access_key>'
```

###### Step 02: Verify the IAM Auth tokens
```sh
apt install awscli -y
aws sqs list-queues --region ap-south-1
```
![](../images/distributed-system-patterns-single-node/21.WPA_IAM_Permissions.png)

###### Step 03: Download the Worker Pod Autoscaler & Create the WPA CRD:
```sh
git clone https://github.com/practo/k8s-worker-pod-autoscaler.git
cd k8s-worker-pod-autoscaler/
./hack/install.sh
```

###### Step 04: Create a deployment where PODs are to be scaled:
```
controlplane $ cat artifacts/examples/example-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: example-deployment
spec:
  selector:
    matchLabels:
      app: example-deployment
  replicas: 1
  template:
    metadata:
      labels:
        app: example-deployment
    spec:
      containers:
      - name: nginx
        image: nginx:1.7.9
        ports:
        - containerPort: 80
controlplane $ kubectl create -f artifacts/examples/example-deployment.yaml
```


###### Step 05: Create WPA object to scale the target deployment depending upon the number of pending message:
```
apiVersion: k8s.practo.dev/v1
kind: WorkerPodAutoScaler
metadata:
  name: example-wpa
spec:
  minReplicas: 0
  maxReplicas: 10
  deploymentName: example-deployment
  queueURI: https://sqs.ap-south-1.amazonaws.com/{{aws_account_id}}/{{queue_prefix-queue_name-queue_suffix}}
  targetMessagesPerWorker: 2
  secondsToProcessOneJob: 0.03
  maxDisruption: "100%"

kubectl create -f example-wpa.yaml
```


###### Step 06: Ensure that the WPA CRD is deployed with proper arguments, especially the region
```
kubectl edit deployment -n kube-system workerpodautoscaler
spec:
      containers:
      - command:
        - /workerpodautoscaler
        - run
        - --resync-period=20
        - --wpa-threads=10
        - --aws-regions=ap-south-1
        - --sqs-short-poll-interval=20
        - --sqs-long-poll-interval=20
        - --k8s-api-qps=5.0
        - --k8s-api-burst=10
        - --wpa-default-max-disruption=100%
        - --queue-services=sqs,beanstalkd
        - -v=2
        env:
        - name: AWS_ACCESS_KEY_ID
          value: AKIAZQRCZZFALMQVFDS2
        - name: AWS_SECRET_ACCESS_KEY
          value: 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
        image: public.ecr.aws/practo/workerpodautoscaler:v1.6.0
        imagePullPolicy: Always
        name: wpa
        resources:
          limits:
            cpu: 100m
            memory: 100Mi
          requests:
            cpu: 10m
            memory: 20Mi
        terminationMessagePath: /dev/termination-log
        terminationMessagePolicy: File
      dnsPolicy: ClusterFirst
```


###### Step 07: Check the logs for WPA CRD pod, scaling the targetted deployment based on the pending messages on SQS:
```
controlplane $ k logs -f workerpodautoscaler-7d6db54c54-n78tx -n kube-system
I0923 17:37:14.078585       1 controller.go:260] Starting WorkerPodAutoScaler controller
I0923 17:37:14.078740       1 controller.go:263] Waiting for informer caches to sync
I0923 17:37:14.278852       1 controller.go:268] Starting workers



W0923 17:37:45.633912       1 controller.go:438] sample-queue qMsgs: -1, q not initialized, waiting for init to complete
I0923 17:37:54.092360       1 controller.go:458] sample-queue current: 1
I0923 17:37:54.093100       1 controller.go:459] sample-queue qMsgs: 15, desired: 8
I0923 17:37:54.111080       1 controller.go:519] sample-queue scaleOp: scale-up
W0923 17:37:54.128488       1 warnings.go:70] unknown field "status"
I0923 17:38:14.093146       1 controller.go:458] sample-queue current: 8
I0923 17:38:14.093861       1 controller.go:459] sample-queue qMsgs: 15, desired: 8
I0923 17:38:14.094254       1 controller.go:519] sample-queue scaleOp: no scaling operation
W0923 17:38:14.098113       1 warnings.go:70] unknown field "status"
I0923 17:38:34.093225       1 controller.go:458] sample-queue current: 8
I0923 17:38:34.093994       1 controller.go:459] sample-queue qMsgs: 15, desired: 8
I0923 17:38:34.094418       1 controller.go:519] sample-queue scaleOp: no scaling operation
W0923 17:38:34.097632       1 warnings.go:70] unknown field "status"


I0923 17:45:34.108384       1 controller.go:458] sample-queue current: 5
I0923 17:45:34.109130       1 controller.go:459] sample-queue qMsgs: 9, desired: 5
I0923 17:45:34.109542       1 controller.go:519] sample-queue scaleOp: no scaling operation
W0923 17:45:34.112468       1 warnings.go:70] unknown field "status"
I0923 17:45:54.109267       1 controller.go:458] sample-queue current: 5
I0923 17:45:54.109900       1 controller.go:459] sample-queue qMsgs: 9, desired: 5
I0923 17:45:54.110329       1 controller.go:519] sample-queue scaleOp: no scaling operation
W0923 17:45:54.113737       1 warnings.go:70] unknown field "status"

I0923 17:46:14.110353       1 controller.go:458] sample-queue current: 5
I0923 17:46:14.110388       1 controller.go:459] sample-queue qMsgs: 8, desired: 4
I0923 17:46:14.110400       1 scale_operation.go:50] sample-queue scaleDownDelay ignored, lastScaleTime is nil
I0923 17:46:14.116918       1 controller.go:519] sample-queue scaleOp: scale-down
W0923 17:46:14.122092       1 warnings.go:70] unknown field "status"


I0923 17:46:34.111286       1 controller.go:458] sample-queue current: 4
I0923 17:46:34.111960       1 controller.go:459] sample-queue qMsgs: 8, desired: 4
I0923 17:46:34.112331       1 controller.go:519] sample-queue scaleOp: no scaling operation
W0923 17:46:34.117062       1 warnings.go:70] unknown field "status"
I0923 17:46:54.112097       1 controller.go:458] sample-queue current: 4
I0923 17:46:54.112759       1 controller.go:459] sample-queue qMsgs: 8, desired: 4
I0923 17:46:54.113147       1 controller.go:519] sample-queue scaleOp: no scaling operation
W0923 17:46:54.120057       1 warnings.go:70] unknown field "status"

I0923 17:47:14.112293       1 controller.go:458] sample-queue current: 4
I0923 17:47:14.112990       1 controller.go:459] sample-queue qMsgs: 8, desired: 4
I0923 17:47:14.113394       1 controller.go:519] sample-queue scaleOp: no scaling operation
W0923 17:47:14.116763       1 warnings.go:70] unknown field "status"
```

### To be explored:
- The project Worker Pod Autoscaler
    - How the Kubernetes HPA works
    - Scale up and scale down metrics
- Understand Kubernetes HPA more in-depth


### References:
1. [Scaling based on Amazon SQS](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-using-sqs-queue.html)
2. [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
3. [Launching Worker Pod Autoscaler — Solving specific problems with worker scaling in Kubernetes](https://medium.com/practo-engineering/launching-worker-pod-autoscaler-3f6079728e8b)
4. [Scaling Kubernetes deployments with Amazon CloudWatch metrics](https://aws.amazon.com/blogs/compute/scaling-kubernetes-deployments-with-amazon-cloudwatch-metrics/)
5. [Worker Pod Autoscaler](https://github.com/practo/k8s-worker-pod-autoscaler)
