curl -X COPY \
http://localhost:3000/api/v1/migrate-daily \
-H 'cache-control: no-cache' \
-H 'client-id: secret' \
-H 'client-secret: id'

channel="notifications"
text="Yesterday tracker data from production moved to historical :raised_hands:"

escapedText=$(echo $text | sed 's/"/\"/g' | sed "s/'/\'/g" )
json="{\"channel\": \"#$channel\", \"text\": \"$escapedText\"}"

curl -s -d "payload=$json" "https://hooks.slack.com/services/xxxxx/xxxxx/xxxx"