import pandas as pd
import statsmodels.api as sm


def counts(df, groupby, wt):
    gdf = df.groupby(groupby)
    count = gdf.size().reset_index(name="count")
    wt = gdf[wt].sum().reset_index(name="wt")
    return pd.concat([count, wt["wt"]], axis=1, sort=False)


def reg(df, dep_var, indep_vars, wt):
    if "const" not in indep_vars:
        indep_vars.append("const")
    model = sm.WLS(df[dep_var], df[indep_vars], weights=df[wt])
    results = model.fit()
    return results.params


def predict(df, indep_vars):
    """
    Assumes that both the independent variables and parameters
    are in the DataFrame
    """
    params = list("param_" + pd.Series(indep_vars))
    x = df[indep_vars]
    p = df[params]
    yhat = x.mul(p.values, axis="index").sum(axis=1)
    return yhat


def match(
    recipient: pd.DataFrame,
    donor: pd.DataFrame,
    recipient_id: str,
    donor_id: str,
    recipient_wt: str,
    donor_wt: str,
    predict_var: str,
    match_on: list,
    groupby: list = None,
    eps=0.001,
):
    """
    Function to iterate through both files and match them with their
    closest record
    Parameters
    ----------
    recipient: pandas DataFrame with the recipient file
    donor: pandas DataFrame with the donor file
    recipient_id: record ID variable in the recipient file
    donor_id: record ID variable in the donor file
    recipient_wt: weight variable in the recipient file
    donor_wt: weight variable in the donor file
    predict_var: variable to be predicted for the match
    match_on: list of variables to match on
    groupby: optional list of variables to partition the data on
    eps: tolerance for using up the weights

    Returns
    -------
    A DataFrame containing the new weights for each record and the match IDs
    """
    recipient = recipient.copy()
    donor = donor.copy()
    donor_list = []  # list to store IDs from donor file
    recipient_list = []  # list to store IDs from recipient
    cwt_list = []  # list to hold the new weights
    diffs = []  # list to hold difference in match values

    # get cell counts and ID's if they partition
    if groupby:
        d_count = counts(donor, groupby, donor_wt)
        d_count.rename(columns={"count": "d_count", "wt": "d_wt"}, inplace=True)
        r_count = counts(recipient, groupby, recipient_wt)
        r_count.rename(columns={"count": "r_count", "wt": "r_wt"}, inplace=True)
        full_count = pd.merge(r_count, d_count, on=groupby, how="inner")
        full_count["cellid"] = full_count.index + 1
        full_count["factor"] = full_count["r_wt"] / full_count["d_wt"]
        donor = pd.merge(donor, full_count, on=groupby, how="inner")
        recipient = pd.merge(recipient, full_count, on=groupby, how="inner")
    # otherwise we give everyone the same cell ID to loop over later
    else:
        donor["cellid"] = 1
        recipient["cellid"] = 1
        factor = recipient[recipient_wt].sum() / donor[donor_wt].sum()
        recipient["factor"] = factor
        donor["factor"] = factor
    donor[donor_wt] *= donor["factor"]

    # run regression on each cell id
    gdf = recipient.groupby("cellid", as_index=False)
    params = gdf.apply(reg, dep_var=predict_var, indep_vars=match_on, wt=recipient_wt)
    params = params.add_prefix("param_")
    params["cellid"] = params.index + 1
    donor = pd.merge(donor, params, on="cellid", how="inner")
    recipient = pd.merge(recipient, params, on="cellid", how="inner")

    donor["yhat"] = predict(donor, match_on)
    recipient["yhat"] = predict(recipient, match_on)

    # loop through each cell ID and find matches
    cell_ids = recipient["cellid"].unique()
    for cid in cell_ids:
        _donor = donor[donor["cellid"] == cid]
        _recipient = recipient[recipient["cellid"] == cid]
        _donor = _donor.sort_values("yhat", kind="mergesort")
        _recipient = _recipient.sort_values("yhat", kind="mergesort")

        # convert to list of dictionaries
        _donor = _donor.to_dict("records")
        _recipient = _recipient.to_dict("records")

        j = 0
        bwt = _donor[j][donor_wt]
        count = len(_donor) - 1
        for record in _recipient:
            awt = record[recipient_wt]
            while awt > eps:
                # weight of new record will be min of
                # records being matched
                cwt = min(awt, bwt)
                recipient_seq = record[recipient_id]
                donor_seq = _donor[j][donor_id]
                # append each sequence to respective list
                donor_list.append(donor_seq)
                recipient_list.append(recipient_seq)
                cwt_list.append(cwt)
                diff = record["yhat"] - _donor[j]["yhat"]
                diffs.append(diff)
                # recalculate weights
                awt = max(0, awt - cwt)
                bwt = max(0, bwt - cwt)
                if bwt <= eps:
                    if j < count:
                        j += 1
                        bwt = _donor[j][donor_wt]

    _match = pd.DataFrame(
        {
            "donor": donor_list,
            "recip": recipient_list,
            "matched_weight": cwt_list,
            "diff": diffs,
        }
    )
    del recipient, donor
    return _match
