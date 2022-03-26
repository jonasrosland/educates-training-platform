JDK11 Environment
=================

This repository contains files to build up a custom workshop dashboard
container image which includes JDK 11, maven and gradle.

The built contained image is hosted at:

```
quay.io/eduk8s/jdk11-environment:master
```

It can be used as a base image for constructing a custom workshop image
which includes workshop content, or can be used as the workshop image
declared in the workshop YAML definition, with workshop files pulled down
from a GitHub repository when the workshop session is created.

```
apiVersion: training.eduk8s.io/v1alpha2
kind: Workshop
metadata:
  name: lab-java-workshop
spec:
  title: Java Workshop
  description: Workshop on developing using Java.
  content:
    image: quay.io/eduk8s/jdk11-environment:master
    files: github.com/eduk8s-tests/lab-java-workshop
```
