from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage


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

string_fs = """
features_selection <- function(DT, survObjT) { 
Nf <- 24 #Number of features to be selected for final model
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
                      "-",
                      HR.confint.upper,
                      ")")
  res <- c(beta, HR, wald.test, p.value) #save results
  names(res) <- c("beta", "HR", "wald.test",
                  "p.value")
  return(res)
})
res <- t(as.data.frame(univ_results, check.names = FALSE))
univariate_results <- as.data.frame(res)

##remove all features that do not have a (highly) significant impact on OS, using p-value of 0.0005
filtered_uv_results <-
  univariate_results[as.numeric(as.character(univariate_results$p.value)) < 0.005, ]
##If not enough highly significant features, then only select significant features (p<0.05)
if (nrow(filtered_uv_results) < Nf) {
  filtered_uv_results <-
    univariate_results[as.numeric(as.character(univariate_results$p.value)) < 0.05, ]
}
##use the Hazard ratio (HR) to select the top #Nf features for model building
## Extract hazard ratio
HR <-
  as.numeric(levels(filtered_uv_results$HR))[filtered_uv_results$HR]
## Create modified HR for ranking
inverseHR <- function(x) {
  if (x < 1) {
    return(1 / x)
  } else{
    return(x)
  }
}
IHR <- sapply(HR, inverseHR)
## sort results by modified HR
sorted_uv_results <-
  sort(IHR, index.return = TRUE, decreasing = TRUE)

##Names of features used, this will have to be different for every method
features <-
  names(filtered_uv_results$beta[sorted_uv_results$ix[1:Nf]])
  }
"""

string_cox = """
cox_model <- function(DT, survObjT, features) { 
##create multivariate Cox regression analysis using selected number of features
fmla <-
  as.formula(paste("survObjT ~ ", paste((
    features
  ), collapse = "+")))
##MODEL BUILDING
##FOR SURVIVAL, WE WILL ONLY EXPLORE the Cox Proportional Hazards regresssion model

coxRegNewT <- cph(fmla, data = DT, x = TRUE, y = TRUE)

##split into strata
nDataT = DT[features]
##create survival predictions
predictionsT <- survest(coxRegNewT, nDataT, times=12)
##calculate median OS based on predictions for splitting of KM curve
medianPSP <- median(predictionsT$surv)
##create model strata vector on predictions of training data using median from training data 
ModelStrataT <-
  as.vector(as.numeric(predictionsT$surv > medianPSP))
## Calculate C-index for Training
CI <- rcorr.cens(predictionsT$surv, survObjT)["C Index"]
#p-value of Kaplan-Meier split
sdfT <- survdiff(survObjT ~ ModelStrataT)
PvalT <- 1 - pchisq(sdfT$chisq, length(sdfT$n) - 1)

## Calculate C-index for validation
CI <- rcorr.cens(predictionsT$surv, survObjT)["C Index"]

#p-value of Kaplan-Meier split
sdf <- survdiff(survObjT ~ ModelStrataT)
PvalT <- 1 - pchisq(sdf$chisq, length(sdf$n) - 1)

KaplanMeierCurveT<-survfit(survObjT ~ ModelStrataT, data = nDataT)
}
"""
r_univariate = SignatureTranslatedAnonymousPackage(
    string_univariate, "univariate_analysis")

r_festures_selection = SignatureTranslatedAnonymousPackage(
    string_fs, "features_selection")

r_cox_model = SignatureTranslatedAnonymousPackage(
    string_cox, "cox_model")
