#!/bin/bash
gcloud compute ssh techtradis@staging --command 'cd ~/projects/tradis/ && ./deploy-staging-director.sh'