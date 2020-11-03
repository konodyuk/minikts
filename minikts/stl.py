import pandas as pd

def empty_like(df):
    """Returns an empty dataframe, preserving only index

    Examples:
        >>> def some_feature(df):
        ...     res = stl.empty_like(df)
        ...     res["col"] = ...
        ...     return res
    """
    return df[[]].copy()

def identity(df):
    """Returns input dataframe

    Examples:
        >>> fs = stl.concat(stl.identity, one_feature, another_feature, ...)
    """
    return df

def _call(feature, df, **k):
    try:
        return feature(df, **k)
    except TypeError:
        return feature(df)

def concat(*features):
    """Concatenates input features

    Args:
        *features: list of features

    Returns:
        Single feature whose output is concatenation of outputs of input features

    Examples:
        >>> cat_cols = ["a", "b", "c"]
        >>> num_scaler = StandardScaler()
        >>> ohe_enc = OneHotEncoder(sparse=False)
        >>> fs = concat(
        ...     compose(select(*numeric), apply_transformer(num_scaler, "num_scaler")),
        ...     compose(
        ...         select(*cat_cols),
        ...         apply_transformer(ohe_enc, "ohe_enc")
        ...     )
        ... )
        >>> x_train = fs(df_train, is_train=True).values
        >>> y_train = df_train.y.values
        >>> x_test = fs(df_test, is_train=False).values
        >>> y_test = df_test.y.values
    """
    def _concat(df, **k):
        results = []
        for feature in features:
            results.append(_call(feature, df, **k))
        return pd.concat(results, axis=1)
    return _concat

def compose(*features):
    """Composes input features sequentially

    Each next feature receives output of a previous one as input.

    Args:
        *features: list of features

    Returns:
        Single feature whose output is the resulf of sequential application of input features

    Examples:
        >>> cat_cols = ["a", "b", "c"]
        >>> num_scaler = StandardScaler()
        >>> ohe_enc = OneHotEncoder(sparse=False)
        >>> fs = concat(
        ...     compose(select(*numeric), apply_transformer(num_scaler, "num_scaler")),
        ...     compose(
        ...         select(*cat_cols),
        ...         apply_transformer(ohe_enc, "ohe_enc")
        ...     )
        ... )
        >>> x_train = fs(df_train, is_train=True).values
        >>> y_train = df_train.y.values
        >>> x_test = fs(df_test, is_train=False).values
        >>> y_test = df_test.y.values
    """
    def _compose(df, **k):
        res = df
        for feature in features:
            res = _call(feature, res, **k)
        return res
    return _compose

def drop(*columns):
    """Drops columns from input dataframe

    Args:
        *columns: list of columns to be dropped

    Returns:
        Feature whose output contains all but dropped columns

    Examples:
        >>> cat_cols = ["a", "b", "c"]
        >>> ohe_enc = OneHotEncoder(sparse=False)
        >>> compose(
        ...     select(*cat_cols),
        ...     drop("month", "day_of_week"),
        ...     apply_transformer(ohe_enc, "ohe_enc")
        ... )
    """
    def _drop(df, **k):
        return df.drop(list(columns), axis=1)
    return _drop

def select(*columns):
    """Selects columns from input dataframe

    Args:
        *columns: list of columns to be selected

    Returns:
        Feature whose output contains only selected columns

    Examples:
        >>> cat_cols = ["a", "b", "c"]
        >>> ohe_enc = OneHotEncoder(sparse=False)
        >>> compose(
        ...     select(*cat_cols),
        ...     drop("month", "day_of_week"),
        ...     apply_transformer(ohe_enc, "ohe_enc")
        ... )
    """
    def _select(df, **k):
        return df[list(columns)]
    return _select

def apply_transformer(transformer, name=None, argument_mapper=None):
    """Applies sklearn-compatible transformer to input dataframe

    Relies on `is_train` keyword to determine whether to call
    `fit_transform` or `transform`. If output of the transformer is
    an instance of pd.DataFrame, then returns it as it is. In case if
    it is an instance of np.ndarray, converts it to pd.DataFrame with
    column names formatted as f"{name}_{i}" for i in [0, width of np.ndarray)

    Args:
        transformer: transformer instance
        name: 
            prefix of output columns 
            (needed only if transformer returns not pd.DataFrame, but np.ndarray)
        argument_mapper: stl.argument_mapper to handle custom interface of transformer

    Returns:
        Feature whose output contains output of transformer

    Examples:
        >>> cat_cols = ["a", "b", "c"]
        >>> cat_enc = CatBoostEncoder(cols=cat_high_cardinality)
        >>> cat_scaler = StandardScaler()
        >>> fs = concat(
        ...     ...,
        ...     compose(
        ...         apply_transformer(cat_enc, "cat_enc", argument_mapper(X=select(*cat_cols), y=select("log_price"))),
        ...         apply_transformer(cat_scaler, "cat_scaler")
        ...     )
        ... )
        >>> x_train = fs(df_train, is_train=True).values
        >>> y_train = df_train.log_price.values
        >>> x_test = fs(df_test, is_train=False).values
        >>> y_test = df_test.log_price.values
    """
    def _apply_transformer(df, **k):
        kw = dict(X=df)
        if argument_mapper is not None:
            kw = argument_mapper(df)
        if k["is_train"]:
            res = transformer.fit_transform(**kw)
        else:
            res = transformer.transform(**kw)
        if not isinstance(res, pd.DataFrame):
            res = pd.DataFrame(res, index=df.index, columns=[f"{name}_{i}" for i in range(res.shape[1])])
        else:
            assert np.all(res.index == df.index)
        return res
    return _apply_transformer

def argument_mapper(**kwargs):
    """Applies multiple features to input dataframe and returns results as a dictionary

    Receives pairs of keyword names and features. When called from a dataframe,
    returns a dictionary whose keys are identical to keyword names and values
    are results of applications of the corresponding features.

    Args:
        *kwargs: pairs of format `{keyword name}: {feature}`

    Returns:
        Function whose output is dict consisting of pairs of format `{keyword name}: {output of feature}`

    Examples:
        >>> cat_cols = ["a", "b", "c"]
        >>> cat_enc = CatBoostEncoder(cols=cat_high_cardinality)
        >>> cat_scaler = StandardScaler()
        >>> fs = concat(
        ...     ...,
        ...     compose(
        ...         apply_transformer(cat_enc, "cat_enc", argument_mapper(X=select(*cat_cols), y=select("log_price"))),
        ...         apply_transformer(cat_scaler, "cat_scaler")
        ...     )
        ... )
        >>> x_train = fs(df_train, is_train=True).values
        >>> y_train = df_train.log_price.values
        >>> x_test = fs(df_test, is_train=False).values
        >>> y_test = df_test.log_price.values
    """
    def _argument_mapper(df):
        res = dict()
        for key, transform in kwargs.items():
            res[key] = transform(df)
        return res
    return _argument_mapper
