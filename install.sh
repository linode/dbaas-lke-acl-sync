#!/bin/bash

read -p "Enter the Kubernetes namespace to install into: " NAMESPACE

if [ -z "$NAMESPACE" ]; then
  echo "Namespace cannot be empty."
  exit 1
fi

kubectl get namespace "$NAMESPACE" >/dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Namespace '$NAMESPACE' does not exist. Creating it..."
  kubectl create namespace "$NAMESPACE"
fi

for file in ./k8s/*.yaml ./k8s/*.yml; do
  [ -e "$file" ] || continue
  echo "Applying $file to namespace $NAMESPACE"
  kubectl apply -n "$NAMESPACE" -f "$file"
done

echo "✅ All manifests applied to namespace '$NAMESPACE'."
