class Patterns:
    """Common patterns for stdout parsing

    Examples:
        >>> import minikts.api as kts
        >>> from lightgbm import LGBMClassifier
        >>> with kts.parse_stdout(kts.patterns.lightgbm, kts.MatplotlibCallback(interval=50)):
        ...     model = LGBMClassifier(n_estimators=1000)
        ...     model.fit(x_train, y_train, eval_set=[(x_train, y_train), (x_test, y_test)])
        >>> with kts.parse_stdout(kts.patterns.lightgbm_valid_only, kts.MatplotlibCallback(interval=50)):
        ...     model = LGBMClassifier(n_estimators=1000)
        ...     model.fit(x_train, y_train, eval_set=[(x_test, y_test)])

        >>> from catboost import CatBoostClassifier
        >>> with kts.parse_stdout(kts.patterns.catboost, kts.MatplotlibCallback(interval=50)):
        ...     model = CatBoostClassifier(n_estimators=1000)
        ...     model.fit(x_train, y_train, eval_set=(x_test, y_test)])
        >>> with kts.parse_stdout(kts.patterns.catboost, kts.MatplotlibCallback(interval=50)):
        ...     model = CatBoostClassifier(n_estimators=1000)
        ...     model.fit(x_train, y_train])

        >>> from lightfm import LightFM
        >>> with kts.parse_stdout(kts.patterns.lightfm, kts.MatplotlibCallback(interval=2)):
        ...     model = LightFM()
        ...     model.fit(interactions, epochs=100, verbose=True)
    """

    catboost = ("learn: {train:f}", "test: {valid:f}", "{step:d}:")
    xgboost_valid_only = ("valid{}:{valid:f}", "[{step:d}]")
    lightgbm_valid_only = ("valid{}:{valid:f}", "[{step:d}]")
    xgboost = ("valid{}0{}:{train:f}", "valid{}1{}:{valid:f}", "[{step:d}]")
    lightgbm = ("valid{}0{}:{train:f}", "valid{}1{}:{valid:f}", "[{step:d}]")
    lightfm = ("{}{epoch:d}", "{}{step:d}")