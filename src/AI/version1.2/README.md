# ML README

*Note: This document is a draft. Will be updated progressively in the near future.*

## 1. Introduction

This is the setup for the exploration and training of ML models that predict cryptocurrency movements over some time frames. 
This is strictly machine learning, with no logic on how to invest once we predict the future. You'll find this logic in 
other parts of the bigger project (see Director). 

There are two ways of working: you can either try single models with the run.py and test.py files or work with hypersearch.py, 
which automatically explores hyperoptimization parameters.

## 2. Setup

1. Python 3.6+.
1. You need to install most of the modules specified in the requirements.txt, but not all; at some point I need to clean it.
1. Install mongodb and populate a database with the data we have in AWS. **Note**: maybe you don't need to, if you already 
gave csv files with data.
1. **Only for hypersearch:** Install PostgreSQL version 10+ and create a database called 'runs_v1'. You also need to change the specifications in
config.yml to match your port, connection name, password, etc.
1. **Only for hypersearch:** Run database.py in the database folder to create the tables to store info from the runs.

*Note:* you'll wanna run this on a GPU rig with some RAM. I'm using a 1060 and 16GB RAM. This is the barest minimum. You can 
use a standard PC, no GPU (CPU-only); in that case pip install -I tensorflow==1.5.0rc1 (instead of tensorflow-gpu). 
The only downside is performance; CPU is **way** slower than GPU for ConvNet computations. 

## 3. Data

There are two ways of populating data; directly from the db or through csv files. 

1. From database: populate a mongodb database with data from AWS. Then, specify a starting date in either the run or hypersearch files
and replace data.import_from_csv() with data.import_from_db(). You also need to choose the number of days for each set of training data. 
I do not recommend more than 10-15 days since otherwise RAM explodes. **Note:** for some reason importing directly from 
database is horribly slow, so this is not recommended for the moment.
1. From csv: place all the csv you want in the data directory. Choose how many csv you want to use as training and testing 
data in the config.yml file (n_test_files and n_train_files). You are all set.

## 3. Hypersearch

The crux of this whole thing is finding the right hyper-parameter combo (things like neural-network width/depth, L1 / L2 / Dropout numbers, 
etc). Some papers have listed optimal default hypers. But in my experience, they don't work well for our purposes (time-series / trading). 
The file hypersearch.py will search hypers forever, ever honing in on better and better combos (using TPE (Tree-structured Parzen Estimator)). 

The goal of the search is to minimize Mean Squared Residual Average of the predictions. Maybe we need to think about this at 
some point. 

**Note:** the hypersearch is capable of switching models, so the differences between two cosecutive runs can be enormous. 
You might want to find the best combos for each kind of models or search reduced spaces or something like that, otherwise the
search can take forever. 

## 4. Run

Once you have a good combo (or not) you might want to run it by itself with all data. The good part about this is that the 
test.py program not only predicts with new data but also simulates investments and returns amount gained or lost.

## 5. Visualization

There is minimal implementation of visualizing the final amount of money and so on, but this needs quite a lot of work.

## 6. Regression vs Classification

You'll see in the model.py file that there are a few classification models, which is something that doesn't make much sense.
I created them to be able to evaluate models better; i.e., with the regression we have RSME, so we can know if a model is better
than another one, but I was looking for an absolute value of how good is a model, and the classification models can give us that. 
We split the coins in "going up" or "not going up" so that in the end we can get an overall accuracy. Don't be fooled by
good accuracies (~65%), every time I have gotten them is because the model was never changing coins, just finding the best 
ones overall. 

# Warning!

Right now the main problem is that models predict tolerably well if you look at RMSE or amount gained **but**, 
and I can't stress this but enough, there is a huge problem, and that is that they always predict the same for each coin. 
I.E., they will pick their favourite coin and won't even look at current data; they'll always stick to that coin. This is 
a general problem with all models that do not overfit. This is obviously a critical bottleneck and needs to be overcome
before moving further. 

**Note:** this is also important for v2 (RL) models, since we need to feed them good data.
