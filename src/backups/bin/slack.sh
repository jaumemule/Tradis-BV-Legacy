#!/bin/bash
channel="notifications"
text="New backup has been uploaded to S3 :moneybag:"

escapedText=$(echo $text | sed 's/"/\"/g' | sed "s/'/\'/g" )
json="{\"channel\": \"#$channel\", \"text\": \"$escapedText\"}"

curl -s -d "payload=$json" "https://hooks.slack.com/services/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"