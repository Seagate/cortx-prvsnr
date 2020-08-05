#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

#!/bin/bash

set -e

#########################
# S3 sanity test script #
#########################

USAGE="USAGE: bash $(basename "$0") [--help]
Run S3 sanity test.
where:
    --help      display this help and exit

Operations performed:
  * Create Account
  * Create User
  * Create Bucket
  * List Buckets
  * Put Object
  * Get Object
  * Delete Object
  * Delete Bucket
  * Create account login profile
  * Get account login proflie
  * Create user login profile
  * Get user login profile"

case "$1" in
    --help )
        echo "$USAGE"
        exit 0
        ;;
esac

s3iamcli=$(s3iamcli CreateAccount -n cloud -e cloud@seagate.com --ldapuser sgiamadmin --ldappasswd ldapadmin)
echo $s3iamcli
access_key=$(echo -e "$s3iamcli" | tr ',' '\n' | grep "AccessKeyId" | awk '{print $3}')
secret_key=$(echo -e "$s3iamcli" | tr ',' '\n' | grep "SecretKey" | awk '{print $3}')

s3iamcli CreateUser -n cloud --ldapuser sgiamadmin --ldappasswd ldapadmin --access_key $access_key --secret_key $secret_key

bucket_name="seagate"
object_name="hello"
Block_count="1"

echo -e "\n\n***** S3: SANITY TEST *****"

TEST_CMD="s3cmd --access_key=$access_key --secret_key=$secret_key"

echo -e "\nCreate bucket - '$bucket_name': "
$TEST_CMD mb "s3://$bucket_name" || { echo "Failed" && exit 1; }

# create a test file
test_file_input=/tmp/"$object_name".input
test_output_file=/tmp/"$object_name".out

dd if=/dev/urandom of=$test_file_input bs=1MB count=$Block_count
content_md5_before=$(md5sum $test_file_input | cut -d ' ' -f 1)

echo -e "\nList Buckets: "
$TEST_CMD ls || { echo "Failed" && exit 1; }

echo -e "\nUpload object '$test_file_input' to '$bucket_name': "
$TEST_CMD put $test_file_input "s3://$bucket_name/$object_name" || { echo "Failed to upload" && exit 1; }

echo -e "\nList uploaded object in '$bucket_name': "
$TEST_CMD ls "s3://$bucket_name/$object_name" || { echo "Failed to list" && exit 1; }

echo -e "\nDownload object '$object_name' from '$bucket_name': "
$TEST_CMD get "s3://$bucket_name/$object_name" $test_output_file || { echo "Failed to download" && exit 1; }
content_md5_after=$(md5sum $test_output_file | cut -d ' ' -f 1)

echo -en "\nData integrity check: "
[[ $content_md5_before == $content_md5_after ]] && echo 'Passed.' || echo 'Failed to check integrity.'

echo -e "\nDelete object '$object_name' from '$bucket_name': "
$TEST_CMD del "s3://$bucket_name/$object_name" || { echo "Failed to delete object" && exit 1; }

echo -e "\nDelete bucket - '$bucket_name': "
$TEST_CMD rb "s3://$bucket_name" || { echo "Failed to delete bucket" && exit 1; }

# delete test files file
rm -f $test_file_input $test_output_file

echo -e "\nCreate account login profile"
s3iamcli  createaccountloginprofile -n cloud --password abcedew --access_key $access_key --secret_key $secret_key

echo -e "\nGet account log inprofile"
s3iamcli  getaccountloginprofile -n cloud --access_key $access_key --secret_key $secret_key

echo -e "\nCreate user login profile"
s3iamcli  createuserloginprofile -n cloud --password abcedew --access_key $access_key --secret_key $secret_key

echo -e "\nGet user login profile"
s3iamcli  getuserloginprofile -n cloud --access_key $access_key --secret_key $secret_key

echo -e "\nDelete Account"
s3iamcli DeleteAccount --force -n cloud --access_key $access_key --secret_key $secret_key

echo -e "\n\n***** S3: SANITY TEST SUCCESSFULLY COMPLETED *****\n"
