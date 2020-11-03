class Patterns:
    catboost = ("learn: {train:f}", "test: {valid:f}", "{step:d}:")
    xgboost_valid_only = ("valid{}:{valid:f}", "[{step:d}]")
    lightgbm_valid_only = ("valid{}:{valid:f}", "[{step:d}]")
    xgboost = ('valid{}0{}:{train:f}', 'valid{}1{}:{valid:f}', '[{step:d}]')
    lightgbm = ('valid{}0{}:{train:f}', 'valid{}1{}:{valid:f}', '[{step:d}]')
