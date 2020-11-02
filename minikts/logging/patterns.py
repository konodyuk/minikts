class Patterns:
    CatBoost = ("learn: {train:f}", "test: {valid:f}", "{step:d}:")
    XGBoost = ("valid{}:{valid:f}", "[{step:d}]")
    LGBM = ("valid{}:{valid:f}", "[{step:d}]")
