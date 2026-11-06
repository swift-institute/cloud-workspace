#!/usr/bin/env bash
case "$1" in
  swift-atoms/*) echo atoms;; swift-molecules/*) echo molecules;;
  swift-compositions/*|swift-institute/*) echo compositions;; coenttb/*) echo coenttb;; *) echo standards;;
esac
