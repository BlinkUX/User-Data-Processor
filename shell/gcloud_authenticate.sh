touch privatekey.json
echo "{\
  \"private_key_id\": \"$GAE_PRIVATE_KEY_ID\",\
  \"private_key\": \"$GAE_PRIVATE_KEY\",\
  \"client_email\": \"$GAE_CLIENT_EMAIL\",\
  \"client_id\": \"$GAE_CLIENT_ID\",\
  \"type\": \"service_account\"\
}" | tee privatekey.json > /dev/null 2> /dev/null
/usr/bin/gcloud auth activate-service-account --key-file privatekey.json
/usr/bin/gcloud config set project "$GAE_PROJECT_ID"
/usr/bin/gsutil -d ls gs://test-user-data-upload