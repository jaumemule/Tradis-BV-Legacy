#!/bin/bash

set -e

currentDir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
projectDir=$currentDir/../app

# RUN build
echo "Start supervisord"
echo "Job succesfully done"

supervisord -n