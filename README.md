# gae-worm
[Google App Engine](https://cloud.google.com/appengine/) Worm is Python based web application designed to expose [GCP](https://cloud.google.com/) settings publicly and clone itself to other projects

This app was created as proof of concept for testing [GCP IAM](https://cloud.google.com/iam/) and answering questions:
* Can GAE app clone itself to other repo using it's [appspot.com service account](https://cloud.google.com/iam/docs/service-accounts#user-managed_service_accounts)?
* Can one service account create keys for other service account?
* Can service account list GCP resources, like other projects and/or service accounts?

## Features

GAE Worm can:
* list GCP resources to which GAE app has access:
  * projects
  * projects IAM
  * service accounts
  * enabled services
* create service account keys for given service account
* enable service for given project
* deploy itself (from Google Cloud Storage bucket) using [GAE Admin API](https://cloud.google.com/appengine/docs/admin-api/)

GCS link to sources: https://storage.googleapis.com/gae-worm/gae-worm-v1.zip

# Setup

Install dependencies:

```
pip install -t lib -r requirements.txt
```

Run locally:

```
dev_appserver.py app.yaml
```
