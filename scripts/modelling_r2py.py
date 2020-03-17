from rpy2.robjects import r, pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import DataFrame
import rpy2.robjects as ro
from rpy2.robjects.conversion import localconverter
import numpy as np
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage
import re


def converter(to_convert, r2pandas=True):

    with localconverter(ro.default_converter + pandas2ri.converter):
        if r2pandas:
            converted = ro.conversion.rpy2py(to_convert)
        else:
            converted = ro.conversion.py2rpy(to_convert)

    return converted


string_univariate=""" 
    univariate_analysis <- function(DT, survObjT) { 
    Nf <- 4 #Number of features to be selected for final model 
    covariates <- colnames(DT) 
    ##save each covariate as individial model formula 
    univ_formulas <- 
      sapply(covariates, function(x) 
        as.formula(paste('survObjT ~', x))) 
    ##create a cox-model for each individual feature 
    univ_models <- 
      lapply(univ_formulas, function(x) { 
        coxph(x, data = DT) 
      }) 
    ## Calculate significance of each feature using the Wald test 
    univ_results <- lapply(univ_models, function(x) { 
      x <- summary(x) 
      p.value <- signif(x$wald["pvalue"], digits = 2) 
      beta <- signif(x$coef[1], digits = 2) 
      #coeficient beta 
      HR <- signif(x$coef[2], digits = 5) 
      #exp(beta) 
      HR.confint.lower <- signif(x$conf.int[, "lower .95"], 2) 
      HR.confint.upper <- signif(x$conf.int[, "upper .95"], 2) 
      wald.test <- paste0(signif(x$wald["test"], digits = 2), 
                          " (", 
                          HR.confint.lower, 
                          "_", 
                          HR.confint.upper, 
                          ")") 
      res <- c(beta, HR, wald.test, p.value) #save results 
      names(res) <- c("beta", "HR", "wald.test", 
                      "p.value") 
      return(res) 
    }) 
    res <- t(as.data.frame(univ_results, check.names = FALSE)) 
    univariate_results <- as.data.frame(res) 
    } 
"""  
r_univariate = SignatureTranslatedAnonymousPackage(
    string_univariate, "univariate_analysis")

# dam = importr('dataAnalysisMisc')
survival = importr('survival')
Data = DataFrame.from_csvfile(
    "/mnt/sdb/test_survival_R/GBM_TP0_T1KM_GTV/combined_csv_new_parfile_training.csv",
    header=True, sep=',')
Surv = survival.Surv
surv_object = Surv(Data[1], Data[2])
Data = converter(Data)
Data = Data[[c for c in Data if c not in ['PID', 'TIME', 'STATUS']]]
corr_matrix = Data.corr().abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(np.bool))
to_drop = [column for column in upper.columns if any(upper[column] > 0.9)]
z = 0
while to_drop:
    to_remove = []
    pval_check = []
    col_index = to_drop[z]
    corr_index = [upper.columns[x[0]] for x in np.where(upper[col_index] > 0.9)]
    sub_data = Data[[c for c in Data if c in corr_index+[col_index]]]
    r_sub_data = converter(sub_data, r2pandas=False)
    res = r_univariate.univariate_analysis(r_sub_data, surv_object)
    res = converter(res)
    hr = [key for key, value in res['HR'].items() if not (np.abs(float(value)) > 0.5 and np.abs(float(value)) < 1.5)
          and not np.abs(float(value)) > 10]
    if hr:
        if len(hr) < len(corr_index+[col_index]):
            to_remove = to_remove + [x for x in corr_index+[col_index] if x not in hr]
        wald = [[key]+re.sub('[()]', '', value.split()[-1]).split('_')
                for key, value in res['wald.test'].items() if key in hr]
        for wald_range in wald:
            key, low, high = wald_range
            if float(low) < 0.9 and float(high) > 1.1:
                to_remove.append(key)
            else:
                pval_check.append(key)
        if pval_check:
            p_values = [[key, value] for key, value in res['p.value'].items()
                        if key in pval_check and float(value) < 0.1]
            if p_values and len(p_values) > 1:
                values = [float(x[1]) for x in p_values]
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
    else:
        z = z+1
    corr_matrix = Data.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(np.bool))
    to_drop = [column for column in upper.columns if any(upper[column] > 0.9)]

res = dam.plotForest(surv_object, data=r_sub_data)
res = converter(sub_data)
