#!/bin/bash

set -e

poetry export -f requirements.txt --output requirements.txt --without-hashes
pip install -r requirements.txt --platform manylinux2014_x86_64 --target ./dependencies --only-binary=:all:
(cd dependencies; zip ../aws_lambda_artifact.zip -r .)
zip aws_lambda_artifact.zip -u .env
zip aws_lambda_artifact.zip -u *.py
zip -ur aws_lambda_artifact.zip routes
(cd dependencies; zip ../aws_lambda_artifact.zip -r .)

echo "Deployment package aws_lambda_artifact.zip created successfully."
