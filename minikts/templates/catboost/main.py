#!/usr/bin/env python

import os
import sys
import time
import click
import shutil
from box import Box
from copy import deepcopy
from glob import glob
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import OneHotEncoder
from category_encoders import CatBoostEncoder

from catboost import CatBoostClassifier
from catboost.datasets import titanic

import minikts.api as kts
from minikts.api import stl, config, hparams
from minikts import utils

kts.init(__file__)
cache = kts.fast_local_cache

# ========== FEATURES ==========

num_cols = ["Pclass", "SibSp", "Age", "Parch", "Fare"]
cat_cols = ["Cabin", "Embarked"]
target = "Survived"

def simple_feature(df):
    res = stl.empty_like(df)
    res["sex"] = (df.Sex == "male") + 0
    return res


# ========== DATASET ==========

class CatBoostTemplateDataset():
    def __init__(self):
        params = hparams.split
        self.splitter = StratifiedKFold(**params)

    def load_train(self):
        self.df_train, _ = titanic()

    def load_test(self):
        _, self.df_test = titanic()
        self.df_test["Survived"] = -1

    def encoders(self):
        ohe = OneHotEncoder()
        cbe = CatBoostEncoder()
        return ohe, cbe

    def features(self, encoders):
        ohe, cbe = encoders
        fs = stl.concat(
            # stl.identity,
            stl.select(*num_cols),
            simple_feature,
            stl.compose(
                stl.select(*cat_cols, target),
                stl.apply_transformer(cbe, "cbe", 
                    argument_mapper=stl.argument_mapper(X=stl.select(*cat_cols), y=stl.select(target))
                ),
            )
        )
        return fs

    def preview(self, idx, dataframe=None, encoders=None, is_train=True, **kw):
        dataframe = dataframe or self.df_train
        encoders = encoders or self.encoders()
        fs = self.features(encoders)
        x_preview = fs(dataframe, is_train=is_train, **kw)
        return x_preview

    def train_folds(self):
        self.load_train()
        y = self.df_train.Survived.values
        for fold_idx, (idx_train, idx_valid) in enumerate(self.splitter.split(y, y)):
            encoders = self.encoders()
            fs = self.features(encoders)
            x_train = fs(self.df_train.iloc[idx_train], is_train=True).values
            x_valid = fs(self.df_train.iloc[idx_valid], is_train=False).values
            y_train = self.df_train.Survived.values[idx_train]
            y_valid = self.df_train.Survived.values[idx_valid]
            cache.save_object(encoders, f"encoders_{fold_idx}")
            data = x_train, y_train, x_valid, y_valid
            yield data, fold_idx

    def test_folds(self):
        self.load_test()
        for fold_idx in range(self.splitter.get_n_splits()):
            encoders = cache.load_object(f"encoders_{fold_idx}")
            fs = self.features(encoders)
            x_test = fs(self.df_test, is_train=False).values
            data = x_test
            yield data, fold_idx


# ========== EXPERIMENT ==========

class CatBoostTemplateExperiment(kts.Experiment):
    @kts.profile()
    def train_fold(self, data, fold_idx):
        x_train, y_train, x_val, y_val = data
        model = CatBoostClassifier(**hparams.catboost)
        with kts.parse_stdout(kts.patterns.catboost, kts.NeptuneCallback(FOLD=fold_idx)):
            model.fit(x_train, y_train, eval_set=[(x_val, y_val)])
        return model

    @kts.profile()
    def score_fold(self, model, data, fold_idx):
        x_train, y_train, x_val, y_val = data
        y_pred = model.predict_proba(x_val)[:, 1]
        score = roc_auc_score(y_val, y_pred)
        kts.logger.log_metric("ROC", fold_idx, score)

    def dataset(self):
        return CatBoostTemplateDataset()

    @kts.profile()
    def predict_fold(self, model, data, fold_idx):
        x = data
        y_pred = model.predict_proba(x)[:, 1]
        return y_pred

    def postprocess(self, outputs):
        outputs = np.array(outputs).T
        raw_outputs = pd.DataFrame(outputs)
        mean_outputs = pd.DataFrame(outputs.mean(axis=1))
        raw_outputs.to_csv("preds.csv", index=False)
        mean_outputs.to_csv(f"submission_{kts.logger.id}.csv", index=False)

    @kts.profile()
    def save_model(self, model, fold_idx):
        cache.save_object(model, f"model_{fold_idx}")

    @kts.profile()
    def load_model(self, fold_idx):
        return cache.load_object(f"model_{fold_idx}")

    @kts.endpoint(create_neptune_experiment=True, copy_sources=True)
    @kts.profile()
    def train(self):
        dataset = self.dataset()
        for data, fold_idx in dataset.train_folds():
            model = self.train_fold(data, fold_idx)
            self.save_model(model, fold_idx)
            self.score_fold(model, data, fold_idx)

    @kts.endpoint(create_neptune_experiment=False, copy_sources=False)
    @kts.profile()
    def test(self):
        dataset = self.dataset()
        outputs = list()
        for data, fold_idx in dataset.test_folds():
            model = self.load_model(fold_idx)
            outputs.append(self.predict_fold(model, data, fold_idx))
        self.postprocess(outputs)

    @kts.endpoint(
        create_neptune_experiment=False, 
        copy_sources=True, 
        experiment_dir=lambda: utils.find_next_of_format("BLEND-{:d}", dir_path=config.paths.root_dir / "blends")
    )
    def ensemble(self, experiment_ids=[9,10]):
        res = 0
        for experiment_id in experiment_ids:
            experiment_path = utils.get_experiment_path(f"MIN-{experiment_id}")
            res += pd.read_csv(experiment_path / "preds.csv")
        res.to_csv(f"preds_blend_{'_'.join(map(str, experiment_ids))}.csv", index=False)


# ========== UTILS ==========


# ========== MAIN ==========

if __name__ == "__main__":
    exp = CatBoostTemplateExperiment()
    exp.run()
    kts.profiler.report()
