#!/bin/bash

result=$(docker build -t lke-dbaas-acl-sync-service-demo:latest .)
if [ $? -ne 0 ]; then  
  echo "$result"
  echo "❌ Failed creating the image."
  exit
fi

echo "✅ Container Image Created: 'lke-dbaas-acl-sync-service-demo:latest'"