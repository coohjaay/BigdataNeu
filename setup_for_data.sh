#!/bin/bash

if [ ! -d data/BF-Open-Data ]; then
  git clone --filter=blob:none --no-checkout https://github.com/Berliner-Feuerwehr/BF-Open-Data data/BF-Open-Data
  cd data/BF-Open-Data
  git sparse-checkout init --cone
  git sparse-checkout set Datasets/Daily_Data Datasets/Mission_Data Datasets/Dispatchcodes
  git checkout main
else
  cd data/BF-Open-Data && git pull
fi


