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
features_selection <- function(DT, survObjT, max_features) { 
Nf <- max_features #Number of features to be selected for final model
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
  univariate_results[as.numeric(sub(",", ".", as.character(univariate_results$p.value), fixed = TRUE)) < 0.005, ]
##If not enough highly significant features, then only select significant features (p<0.05)
if (nrow(filtered_uv_results) < Nf) {
  filtered_uv_results <-
    univariate_results[as.numeric(sub(",", ".", as.character(univariate_results$p.value), fixed = TRUE)) < 0.05, ]
}
##use the Hazard ratio (HR) to select the top #Nf features for model building
## Extract hazard ratio
HR <-
  as.numeric(sub(",", ".", levels(filtered_uv_results$HR), fixed = TRUE))[filtered_uv_results$HR]
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

res = list(strata=ModelStrataT, km = KaplanMeierCurveT,  data = nDataT, surv_obj=survObjT)
return(res)
}
"""

string_survplot = """
survival_plot <- ggsurvplot(
  KaplanMeierCurveT,        # survfit object with calculated statistics.
  data = nDataT,
  pval = TRUE,              # show p-value of log-rank test.
  xlim = c(0, 98),          # set x-axis limits
  conf.int = TRUE,          # show confidence intervals for 
  # point estimates of survival curves.
  conf.int.style = "step",  # customize style of confidence intervals
  xlab = "Time in months",  # customize X axis label.
  break.time.by = 12,       # break X axis in time intervals.
  ggtheme = theme_bw(),     # customize plot and risk table with a theme.
  risk.table = "abs_pct",   # absolute number and percentage at risk.
  risk.table.y.text.col = T,# colour risk table text annotations.
  risk.table.y.text = FALSE,# show bars instead of names in text annotations
  # in legend of risk table.
  ncensor.plot = FALSE,      # plot the number of censored subjects at time t
  surv.median.line = "hv",  # add the median survival pointer.
  legend.labs = 
    c("Group1", "Group2"),    # change legend labels.
  palette = 
    c("#E7B800", "#2E9FDF") # custom color palettes.
)
"""


string_subsample = """
subsample <- function(DT, OST, CST, features) { 
nDataT = DT[features]

DT.cox <- nDataT
DT.cox$OST = OST
DT.cox$CST = CST
# specifiy the resampling tech, k-fold cross validation
ss = makeResampleDesc("Subsample", iters=500, split=6/7)
cox.task = makeSurvTask(data=DT.cox, target=c("OST", "CST"))
cox.lrn <- makeLearner("surv.coxph")
cox.kFoldCV = resample(learner=cox.lrn, cox.task, ss, show.info=FALSE, models=TRUE)
}
"""


string_repcv = """
rep_cv <- function(DT, OST, CST, features) { 
nDataT = DT[features]

DT.cox <- nDataT
DT.cox$OST = OST
DT.cox$CST = CST
# specifiy the resampling tech, k-fold cross validation
ss = makeResampleDesc("RepCV", folds = 7, reps =200)
cox.task = makeSurvTask(data=DT.cox, target=c("OST", "CST"))
cox.lrn <- makeLearner("surv.coxph")
cox.kFoldCV = resample(learner=cox.lrn, cox.task, ss, show.info=FALSE, models=TRUE)
}
"""

string_lasso = """
lasso <- function(DT, survObjT) {
x = as.matrix(DT)

## Run the code below to load the function into workspace. This function performs a #nrep repeated 10-fold
## cross-validation, which is intended to stabilize the method and to find the optimal lambda with the smallest error.
glmnet.repcv <- function(x,survObjT,nreps,measure = c("mse", "deviance", "class", "auc", "mae"),
                         family=c("gaussian","binomial","poisson","multinomial","cox","mgaussian"),pen){
  CVMs <- NULL
  CVSDs <- NULL
  dfmax = 5 #set the maximum number of degrees-of-freedom
  measure = match.arg(measure)
  lambda.mins <- NULL #list of minimum error lambdas
  lambda.1ses <- NULL #list of 1se lambdas
  for (i in 1:nreps){
    if (missing(pen))
      ##perform 1 cross-validation (default: 10 folds)
      cv <- cv.glmnet(x,survObjT,alpha=1,family=family,type.measure=measure,dfmax=dfmax)
    else
      ##perform 1 cross-validation (default: 10 folds)
      cv <- cv.glmnet(x,survObjT,alpha=1,family=family,type.measure=measure,penalty.factor=pen,dfmax=dfmax)
    CVMs  <- qpcR:::cbind.na(CVMs,  cv$cvm) #store partial likelihood deviances
    CVSDs <- qpcR:::cbind.na(CVSDs, cv$cvsd) #store standard errors
    lambda.mins = c(lambda.mins,cv$lambda.min) #store lambda.min for each run
    lambda.1ses = c(lambda.1ses,cv$lambda.1se) #store lambda.1se for each run
  }
  rownames(CVMs) <- cv$glmnet.fit$lambda[1:nrow(CVMs)]; colnames(CVMs) <- NULL;
  mean.CVMs = rowMeans(CVMs,na.rm=TRUE)
  mean.CVSDs = rowMeans(CVSDs,na.rm=TRUE)
  if (measure=="auc")
    lambda.min.index = which.max(mean.CVMs) #max mean AUC
  else
    lambda.min.index = which.min(mean.CVMs) #min mean error
  
  lambda.min <- as.numeric(sub(",", ".", names(lambda.min.index), fixed = TRUE))
  if (measure=="auc")
    ## which.max returns the first TRUE
    lambda.1se.index = which.max(mean.CVMs > max(mean.CVMs)-mean.CVSDs[lambda.min.index])
  else
    ## which.max returns the first TRUE
    lambda.1se.index = which.max(mean.CVMs < min(mean.CVMs)+mean.CVSDs[lambda.min.index])
  lambda.1se <- as.numeric(sub(",", ".", names(lambda.1se.index), fixed = TRUE))
  return(list(lambda.min = lambda.min,lambda.1se = lambda.1se, glmnet.fit = cv$glmnet.fit))
}

## Run #nrep repeated 10-fold CV
nrep = 200 #number of repetitions for repeated cross-validation
measure = "deviance" # partial-likelihood for the Cox model
family  = "cox" # cox model for survival
glmnetSTRUCT = list()
glmnetSTRUCT$glmnet = glmnet.repcv(x,survObjT,nrep,measure=measure,family=family) # x = variables, y = outcome

## Store selected features for reference: lambda.min is the value of lambda that gives minimum mean-cross-validated error
glmnetSTRUCT$selection = coef(glmnetSTRUCT$glmnet$glmnet.fit,s=glmnetSTRUCT$glmnet$lambda.min) # selected features
glmnetSTRUCT$selection = glmnetSTRUCT$selection[which(glmnetSTRUCT$selection!=0),] # selected features + coefficients
glmnetSTRUCT$selection #print selected features + coefficients
features = names(glmnetSTRUCT$selection) # save selected features
}
"""
