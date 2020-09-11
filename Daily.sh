#!/bin/bash
awk 'BEGIN{ sum=0 }
{ sum += $6; print $0 }
END{ print(sum) }' $1
