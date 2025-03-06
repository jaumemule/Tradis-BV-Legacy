#!/bin/bash

while [ $# -gt 0 ]; do
  case "$1" in
    --email=*)
      email="${1#*=}"
      ;;
    --name=*)
      name="${1#*=}"
      ;;
    --exchange=*)
      exchange="${1#*=}"
      ;;
    --key=*)
      key="${1#*=}"
      ;;
    --secret=*)
      secret="${1#*=}"
      ;;
    --passphrase=*)
      passphrase="${1#*=}"
      ;;
    --surname=*)
      surname="${1#*=}"
      ;;
    --environment=*)
      environment="${1#*=}"
      ;;

    *)
      printf "***************************\n"
      printf "* Error: Invalid argument.*\n"
      printf "***************************\n"
      exit 1
  esac
  shift
done

if [ $passphrase == 'no' ]
then
    pphrase=''
else
    pphrase=$passphrase
fi


if [ $environment == 'production' ]
then
    url="https://middleware.tradis.ai/api/v1"


    if [ $exchange == 'binance' ]
    then
        strategyId="5e1f2b7e2014c078ea655c1d"
    elif [ $exchange == 'coinbasepro' ]
    then
        strategyId="5e78862c2014c078ea83dbef"
    else
        printf "\nERROR: Exchange not supported\n"
        exit
    fi


elif [ $environment == 'staging' ]
then
    url="https://middleware.tradis.dev/api/v1"

    if [ $exchange == 'binance' ]
    then
        strategyId="5db19c9e7c213e5561435761"
    elif [ $exchange == 'coinbasepro' ]
    then
        strategyId="5e7f71e93f1ae987227c193e"
    else
        printf "\nERROR: Exchange not supported\n"
        exit
    fi

elif [ $environment == 'dev' ]
then
    url="http://localhost:8071/api/v1"

    if [ $exchange == 'binance' ]
    then
        strategyId="5db19c8b7c213e556143575e"
    elif [ $exchange == 'coinbasepro' ]
    then
        strategyId="5e6fa7720a6dee4939fd6795"
    else
        printf "\nERROR: Exchange not supported\n"
        exit
    fi

else
    printf "\nERROR: Environment not supported\n"
    exit
fi

password="Ilove0Tradis!"

printf "\n"

printf "This will create a user and an exchange account for: \n"

printf "\n"

printf "Exchange: $exchange\n"

printf "\n"

printf "Email: $email\n"
printf "Name: $name\n"
printf "Surname: $surname\n"
printf "Password: $password\n"
printf "\n"

printf "Key: $key\n"
printf "Secret: $secret\n"
printf "Passphrase: $pphrase\n"

printf "\n"

read -p "Are you freakin sure? (y/n) " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1 # handle exits from shell or function but don't exit interactive shell
fi

printf "===========================\n"
printf "Checking or installing dependencies\n"
printf "===========================\n\n\n"

brew list jq || brew install jq

printf "======================================\n"
printf " ---> Dialing in with staging <---- \n"
printf "======================================\n\n\n"

generate_registration()
{
  cat <<EOF
{
  "email": "$email",
  "name": "$name",
  "surname": "$surname",
  "password": "$password"
}
EOF
}

printf "======================================\n"
printf " ---> Registering user <---- \n"
printf "======================================\n\n\n"

registration=$(curl --location --request POST ''"$url"'/user-registration?verified=1' \
--header 'Content-Type: application/json' \
--data-raw "$(generate_registration)" | jq '.')

if [[ $registration == *"error"* ]]; then
    printf "\n============ ERR ===============\n"
        echo $registration
    printf "\n"
    printf        "Stopping... :( \n"
    printf "===========================\n\n\n"
  exit
fi

sleep 1

generate_login()
{
  cat <<EOF
{
	"email" : "$email",
	"password" : "$password"
}
EOF
}

printf "======================================\n"
printf "       ---> Logging in !!! <---- \n"
printf "======================================\n\n\n"


token=$(curl --location --request POST ''"$url"'/user-login' \
--header 'Content-Type: application/json' \
--data-raw "$(generate_login)" | jq '.data.token')

TOKEN="${token//\"}"

printf "======================================\n"
printf " ---> Creating exchange account <---- \n"
printf "======================================\n\n\n"

createAccount()
{
  cat <<EOF

{
  "exchange" : "$exchange",
  "strategyId" : "$strategyId",
  "key" : "$key",
  "secret" : "$secret",
  "passphrase" : "$pphrase"
 }
EOF
}

response=$(curl --location --request POST ''"$url"'/user-accounts' \
--header 'Content-Type: application/json' \
--header 'Authorization: '"$TOKEN"'' \
--data-raw "$(createAccount)" | jq '.')

if [[ $response == *"error"* ]]; then
    printf "\n============ ERR ===============\n"
        echo $response
    printf "\n"
    printf        "Stopping... :( \n"
    printf "===========================\n\n\n"
  exit
fi


verification=$(curl --location --request GET ''"$url"'/user-accounts' \
--header 'Authorization: '"$TOKEN"'' | jq '.[].accountName')

echo $verification


printf "=============================================\n"
printf " ======= TRADIS HAS NOW A NEW USER :P ======= \n"
printf "=============================================\n"


printf "==================================================\n"
printf " ===== PLEASE, IMPORTANT: Store Account Hash  ==== \n"
printf " =======     $verification    ======= \n"
printf "===================================================\n\n\n"

#./createUserAndExchangeAccount.sh --environment=staging --email=jaumemule@tradis.ai --name=Jaume --surname=Mule --exchange=binance --key=xxxx --secret=xxxx --passphrase=no
