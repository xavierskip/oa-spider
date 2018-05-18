#!/bin/bash
result=`ifconfig | grep ppp0 | wc -l`
if [[ $result  != "1" ]]; then
    pon hbwjw
fi
