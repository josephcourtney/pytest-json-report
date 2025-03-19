#!/usr/bin/env sh

coverage run -m pytest
coverage xml
coverage report
