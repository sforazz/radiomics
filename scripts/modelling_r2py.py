from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import DataFrame
import rpy2.robjects as ro
from rpy2.robjects.conversion import localconverter
import numpy as np
import re
from radiomics.r_wrapper import (
    string_cox, string_fs, string_univariate,
    string_survplot, string_subsample, string_repcv, string_lasso)
import rpy2.robjects as robjects
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage
from scipy.stats import skew


def drop_hihgly_corr(Data, to_drop, upper, correlation_th):

    to_keep = []
    for col in to_drop:
        pval_check = []
#         col_index = to_drop[0]
        corr_index = [upper.columns[x[0]] for x in np.where(upper[col] > correlation_th)]
        sub_data = Data[[c for c in Data if c in corr_index+[col]]]
        r_sub_data = converter(sub_data, r2pandas=False)
        res = r_univariate.univariate_analysis(r_sub_data, surv_object)
        res = converter(res)
        hr = [key for key, value in res['HR'].items()
              if not (np.abs(float(value.replace(',', '.'))) > 0.5 and np.abs(float(value.replace(',', '.'))) < 1.5)
              and not np.abs(float(value.replace(',', '.'))) > 10]
        if hr:
#             if len(hr) < len(corr_index+[col]):
#                 to_remove = to_remove + [x for x in corr_index+[col_index] if x not in hr]
            wald = [[key]+re.sub('[()]', '', value.split()[-1]).split('_')
                    for key, value in res['wald.test'].items() if key in hr]
            for wald_range in wald:
                key, low, high = wald_range
                if not(float(low.replace(',', '.')) < 0.9
                       and float(high.replace(',', '.')) > 1.1):
                    pval_check.append(key)
            if pval_check:
                p_values = [[key, value] for key, value in res['p.value'].items()
                            if key in pval_check and float(value.replace(',', '.')) < 0.1]
                if p_values and len(p_values) > 1:
                    values = [float(x[1].replace(',', '.')) for x in p_values]
                    min_pval = np.min(values)
                    temp_to_keep = [p_values[i][0] for i, val in enumerate(values)
                                    if val == min_pval]
                    to_keep = to_keep + temp_to_keep
                elif p_values and len(p_values) == 1:
                    to_keep = to_keep + pval_check
#         else:
#             to_remove = corr_index+[col_index]
#         if to_remove:
#             Data = Data[[c for c in Data if c not in to_remove]]
#             corr_matrix = Data.corr().abs()
#             upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(np.bool))
#             to_drop = [column for column in upper.columns if any(upper[column] > correlation_th)]
#         else:
#             to_drop.remove(col_index)
    
    return list(set(to_keep))


def drop_hihgly_corr_old(Data, to_drop, upper, correlation_th):

    while to_drop:
        to_remove = []
        pval_check = []
        col_index = to_drop[0]
        corr_index = [upper.columns[x[0]] for x in np.where(upper[col_index] > correlation_th)]
        sub_data = Data[[c for c in Data if c in corr_index+[col_index]]]
        r_sub_data = converter(sub_data, r2pandas=False)
        res = r_univariate.univariate_analysis(r_sub_data, surv_object)
        res = converter(res)
        hr = [key for key, value in res['HR'].items()
              if not (np.abs(float(value.replace(',', '.'))) > 0.5 and np.abs(float(value.replace(',', '.'))) < 1.5)
              and not np.abs(float(value.replace(',', '.'))) > 10]
        if hr:
            if len(hr) < len(corr_index+[col_index]):
                to_remove = to_remove + [x for x in corr_index+[col_index] if x not in hr]
            wald = [[key]+re.sub('[()]', '', value.split()[-1]).split('_')
                    for key, value in res['wald.test'].items() if key in hr]
            for wald_range in wald:
                key, low, high = wald_range
                if float(low.replace(',', '.')) < 0.9 and float(high.replace(',', '.')) > 1.1:
                    to_remove.append(key)
                else:
                    pval_check.append(key)
            if pval_check:
                p_values = [[key, value] for key, value in res['p.value'].items()
                            if key in pval_check and float(value.replace(',', '.')) < 0.1]
                if p_values and len(p_values) > 1:
                    values = [float(x[1].replace(',', '.')) for x in p_values]
                    min_pval = np.min(values)
                    temp_to_remove = [p_values[i][0] for i, val in enumerate(values)
                                      if val != min_pval]
                    to_remove = to_remove + temp_to_remove
                elif not p_values:
                    to_remove = to_remove + pval_check
        else:
            to_remove = corr_index+[col_index]
        if to_remove:
            Data = Data[[c for c in Data if c not in to_remove]]
            corr_matrix = Data.corr().abs()
            upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(np.bool))
            to_drop = [column for column in upper.columns if any(upper[column] > correlation_th)]
        else:
            to_drop.remove(col_index)
    
    return Data


def converter(to_convert, r2pandas=True):

    with localconverter(ro.default_converter + pandas2ri.converter):
        if r2pandas:
            converted = ro.conversion.rpy2py(to_convert)
        else:
            converted = ro.conversion.py2rpy(to_convert)

    return converted


# dam = importr('dataAnalysisMisc')
survival = importr('survival')
rms = importr('rms')
ggplot = importr('ggplot2')
survminer = importr('survminer')
caret = importr('caret')
glmnet = importr('glmnet')
mlr = importr('mlr')

r_univariate = SignatureTranslatedAnonymousPackage(
    string_univariate, "univariate_analysis")

r_festures_selection = SignatureTranslatedAnonymousPackage(
    string_fs, "features_selection")

r_cox_model = SignatureTranslatedAnonymousPackage(
    string_cox, "cox_model")

r_subsample = SignatureTranslatedAnonymousPackage(
    string_subsample, "subsample")

r_repcv = SignatureTranslatedAnonymousPackage(
    string_repcv, "rep_cv")

r_lasso = SignatureTranslatedAnonymousPackage(
    string_lasso, "lasso")

accurate_drop = False
# correlation_th = 0.9
thresholds = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
z_scoring = True
log_scale = False

# Data = DataFrame.from_csvfile(
#     "/home/fsforazz/Desktop/test_survival_R/GBM_TP0_T1KM_GTV/combined_csv_new_parfile_training.csv",
#     header=True, sep=',')
# orig_data = DataFrame.from_csvfile(
#     "/home/fsforazz/Desktop/test_survival_R/GBM_TP0_T1KM_GTV/combined_csv_new_parfile_training.csv",
#     header=True, sep=',')

Data = DataFrame.from_csvfile(
    "/mnt/sdb/test_survival_R/GBM_TP0_T1KM_GTV/combined_csv_new_parfile_training.csv",
    header=True, sep=',')
orig_data = DataFrame.from_csvfile(
    "/mnt/sdb/test_survival_R/GBM_TP0_T1KM_GTV/combined_csv_new_parfile_training.csv",
    header=True, sep=',')

Surv = survival.Surv
surv_object = Surv(Data[1], Data[2])
Data = converter(Data)
Data = Data[[c for c in Data if c not in ['PID', 'TIME', 'STATUS']]]
if z_scoring and not log_scale:
    Data = (Data - Data.mean(axis=0))/Data.std(axis=0)
elif log_scale and not z_scoring:
    for col in Data.columns:
        Data[col] = np.log10(Data[col]+1-Data[col].min())
elif log_scale and z_scoring:
    features_skweness = skew(Data, axis=0)
    skew_index = np.where(np.abs(features_skweness) > 1)[0]
    log_col_names = [c for i, c in enumerate(Data.columns) if i in skew_index]
    zscore_col_names = [c for c in Data.columns if c not in log_col_names]
    for col in log_col_names:
        Data[col] = np.log10(Data[col]+1-Data[col].min())
    Data[zscore_col_names] = (Data[zscore_col_names] - Data[zscore_col_names].mean(axis=0))/Data[zscore_col_names].std(axis=0)

normalized_data = Data.copy()
cis = []
for correlation_th in thresholds:
    corr_matrix = normalized_data.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(np.bool))
    to_drop = [column for column in upper.columns if any(upper[column] > correlation_th)]
    
    if accurate_drop:
        keep_index = drop_hihgly_corr(normalized_data, to_drop, upper, correlation_th)
        drop_index = [c for c in normalized_data.columns if c not in keep_index]
        Data = normalized_data.drop(normalized_data[drop_index], axis=1)
    else:
        Data = normalized_data.drop(normalized_data[to_drop], axis=1)
    
#     max_features = int(len(keep_index)/2)
    r_data = converter(Data, r2pandas=False)
    features = r_festures_selection.features_selection(r_data, surv_object, 24)
    try:
        features_lasso = r_lasso.lasso(r_data, surv_object)
        print('Number of features selected by LASSO: {}'.format(len(features_lasso)))
    except:
        print('LASSO failed')
    features = ro.r("na.omit")(features)
    print('Number of features selected by univariate: {}'.format(len(features)))
    KM_object = r_cox_model.cox_model(r_data, surv_object, features)
    robjects.globalenv["nDataT"] = KM_object.rx("data")[0]
    robjects.globalenv["KaplanMeierCurveT"] = KM_object.rx("km")[0]
    robjects.globalenv["ModelStrataT"] = KM_object.rx("strata")[0] 
    robjects.globalenv["survObjT"] = KM_object.rx("surv_obj")[0]
#     subsample = r_subsample.subsample(r_data, orig_data[1], orig_data[2], features)
    rep_cv = r_repcv.rep_cv(r_data, orig_data[1], orig_data[2], features)
    try:
        rep_cv_lasso = r_repcv.rep_cv(r_data, orig_data[1], orig_data[2], features_lasso)
        print('Average C-index repeated CV LASSO: {}'.format(rep_cv_lasso[5]))
    except:
        print('LASSO failed')
#     c_index = subsample[5]
#     print('Average C-index subsample: {}'.format(c_index))
    print('Average C-index repeated CV: {}'.format(rep_cv[5]))
    cis.append(rep_cv[5])
    r_survplot = SignatureTranslatedAnonymousPackage(
        string_survplot, "survival_plot")
    res = r_survplot.survival_plot
    ggplot.ggsave('trainig_set_results_th_{0}_CI_{1}.png'.format(correlation_th, rep_cv[5][0]), res[0], width=20, height=15, units = "cm")
# res = converter(res)
# res = dam.plotForest(surv_object, data=r_sub_data)
# res = converter(sub_data)
print('Done!')
