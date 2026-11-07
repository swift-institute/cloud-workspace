#!/usr/bin/env bash
# Prints every package in tier order: atoms, molecules, standards, compositions (with institute), coenttb.
cd "$(dirname "$0")/.."
{
  grep '^swift-atoms/' repos.txt
  grep '^swift-molecules/' repos.txt
  grep -vE '^(swift-atoms|swift-molecules|swift-compositions|swift-institute)/' repos.txt
  grep -E '^(swift-compositions|swift-institute)/' repos.txt
  cat private-repos.txt
} | grep -v '^$'
