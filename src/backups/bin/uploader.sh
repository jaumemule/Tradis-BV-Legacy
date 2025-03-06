#!/bin/bash
# Usage: ./backupS3
# IDEALLY: s3-put <FILE> <S3_BUCKET> [<CONTENT_TYPE>]
#
# Uploads a file to the Amazon S3 service.
#
# Depends on AWS credentials being set via env (hardcoded now, however)
# - AMAZON_ACCESS_KEY_ID
# - AMAZON_SECRET_ACCESS_KEY
#
# Outputs the URL of the newly uploaded file.

# mongodump -h localhost:27017 -d aggregated -o backup
# BEFORE DO tar -zcvf aggregated.tar.gz backup

# mongorestore -h localhost:27017 -d aggregated .
ntpdate -s time.nist.gov

set -e

authorization() {
  local signature="$(string_to_sign | hmac_sha1 | base64)"
  echo "AWS xxxxxxx:${signature}"
}

hmac_sha1() {
  openssl dgst -binary -sha1 -hmac "xxxxx"
}

base64() {
  openssl enc -base64
}

bin_md5() {
  openssl dgst -binary -md5
}

string_to_sign() {
  echo "$http_method"
  echo "$content_md5"
  echo "$content_type"
  echo "$date"
  echo "x-amz-acl:$acl"
  printf "/$bucket/$remote_path"
}

date_string() {
  LC_TIME=C date "+%a, %d %h %Y %T %z"
}

file="aggregated.tar.gz"
bucket="cryptoreus-backups-production"
content_type="application/x-compressed-tar"

http_method=PUT
acl="public-read"
remote_path="${file##*/}"
content_md5="$(bin_md5 < "$file" | base64)"
date="$(date_string)"

url="https://$bucket.s3-eu-west-1.amazonaws.com/$remote_path"

curl -qsSf -T "$file" \
  -H "Authorization: $(authorization)" \
  -H "x-amz-acl: $acl" \
  -H "Date: $date" \
  -H "Content-MD5: $content_md5" \
  -H "Content-Type: $content_type" \
  "$url"

echo "$url"

echo "BACKUP DONE at $date"