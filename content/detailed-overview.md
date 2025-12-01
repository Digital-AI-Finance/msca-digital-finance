---
title: Detailed overview
date: '2025-12-01'
draft: false
original_url: https://www.digital-finance-msca.com/detailed-overview
images:
- /images/blog/logo_d9d66bb7.jpg
- /images/blog/logo-nobackground-500_dccd868e.png
- /images/general/11062b_ef9712a9c92847bc96513e87dd36c78c_mv2_1fcd35a5.jpg
- /images/general/Screenshot_2022-08-05_at_15_15_31_767cc6d6.png
- /images/general/Fig2_345ca38b.png
- /images/general/Bitcoin_correctly__9cca8a1d.png
- /images/general/Bitcoin_shuffled_77f44ef4.png
- /images/blog/unnamed_c029ae93.png
- /images/blog/1cd49e_46e17462b534409c9a46ee2aad6648ab_mv2_933b9f21.png
- /images/blog/11062b_9e78da3320da497ab23ce28d738d388a_mv2_ae27c472.png
---

# XAI in Finance: Detailed View

" ... bankers are in the business of managing risk, pure and simple, that is the business of banking.” 

– Walter Wriston, former CEO of Citibankitors.

### What we do?

The management of risks, and especially the management of credit risk, is one of the core challenges of financial institutions. By relying extensively on granular customer data and advanced methodologies, Swiss financial institutions can offer a new approach to credit risk evaluation, valid even in a context of very short credit history of clients, one that might not satisfy traditional lending requirements. In other words, the advances in digital technology allow Swiss financial institutions to reduce the cost of credit and increase financial inclusion. Yet, AI-based techniques applied to credit scoring have certain weaknesses, one being that they remain largely incomprehensible, a “black box”, for the nontechnical model evaluators which need to approve them.

![Working with Financial Documents](/images/general/11062b_ef9712a9c92847bc96513e87dd36c78c_mv2_1fcd35a5.jpg)

The proposal of this innovation project is to develop a visual analytics (VA) tool that will be used both by model developers (financial institutions) and model evaluators (regulators) for the purpose of understanding the inner-workings of AI/ML techniques applied to credit scoring. The VA tool will enable users to manipulate the input features and/or model specifications, and observe the resulting change in the outputs of the model (Figure 1). 

![Screenshot 2022-08-05 at 15.15.31.png](/images/general/Screenshot_2022-08-05_at_15_15_31_767cc6d6.png)

##### Figure 1. Concept for the VA tool

The Business Side. One use of the proposed VA tool is in the context of financial institutions developing credit scoring methodologies (i.e. banks as well as FinTech credit providers). In most cases, these companies are familiar with building and developing ML models but might be interested in improving such techniques by running quality checks on an existing platform.

​

The Regulatory Side. The second use case of our proposed VA tool is that of a national regulator reviewing a FinTech lender’s business model. In this context, the regulators need to review the internal credit risk ML-based model to avoid potential weaknesses of a naive application of ML. Being, in most cases, non-experts in ML, regulators need an easy-to-use tool that will allow them to answer the following questions: is the model mimicking the decision-making process of a financial expert or at least responding “rationally” to sets of inputs? Is it “too” sensitive to small changes of the input features? What are potential operational risk issues arising from the model?

### How we do it? 

We build a VA framework that enables users to evaluate two different use cases:

\- credit risk modelling use case 

\- financial time series forecasting use case

Credit Risk Modelling 

In the context of the credit risk use case, the VA tool enables users to manipulate the input features of a specific problem task and observe the resulting change in the outputs of the model. As an end result, the tool will provide a positive or negative score concerning the following aspects of the model performance (Figure 2):

  * “In line with financial logic”. The tool enables users to identify the main features that drive the model’s outputs and obtain an overall score of whether the model is choosing factors that would be selected by a financial expert i.e. whether the specification is in line with financial logic.

  * Robust classification of risk classes

    * The tool enables the users to understand how sensitive the model is to slight changes in input features and provide detailed statistics on the changes incurred as a result of the slight changes in the input space. 

    * The tool also enable the users to see for the overall influence of each input factor on output variations in a specified model

  * Technical robustness

    * Data quality - the tool provides a very detailed overview of the pre-processing and data quality steps necessary for training various ML models on financial data 

    * The tool will provide a high-level quality score measuring the run-time robustness of the  
model with regard to scalability, error-handling, &c.

  * Operational risk impact. The tool identifies the potential operational risk impact of the model under consideration, provide a risk matrix indication, identify critical issues, and suggest necessary mitigation. 

![Fig2.png](/images/general/Fig2_345ca38b.png)

##### Figure 2. Conceptual framework of the VA's functionalities. A user starts by examining the dataset and the association between the different features and the response variable. Once the exploration of the input space is completed, users can check the performance of various trained ML models and make comparison between different models. In the next step, the users can obtain global and local explanations as to how different ML models arrived at the estimated probabilities of default for the various users. Finally, the VA allows users to check that stability and robustness of predictions made.

### Extension: XAI for Financial Time Series 

Going beyond the credit risk use case, the research team identified additional relevant topics concerning the application of existing XAI methods in financial use cases. Namely, even though many of the classical explainability approaches can lead to valuable insights about the models’ inner workings, in most cases these techniques are not tailored for time series applications due to the presence of possibly complex and non-stationary dependence structure of the data. 

​​

Let's imagine a use case in which the objective is to apply a complex ML model for the purpose of predicting the price of the Bitcoin at time t by using several lagged values as dependent variables. 

​

Due to the complex nature of the underlying ML model, it might be difficult for us to infer how the lagged values interact so to arrive at a certain prediction. To address this challenge, we resort to some of the state-of-art methods available in the literature, like [SHAP](https://arxiv.org/abs/1705.07874) and [LIME](https://www.kdd.org/kdd2016/papers/files/rfp0573-ribeiroA.pdf) and obtain some insights into the inner-workings of the underlying ML model. What we find is that the application of these state-of-art approaches to financial time series might not be the best solution. Namely, perturbation-based methods are fully dependent on the ability to perturb samples in a meaningful way. In the context of financial data, this is not the case because of several reasons: 

  * if features are correlated, the artificial coalitions created will lie outside of the multivariate joint distribution of the data

  * if the data are independent, coalitions/generated data points can still be meaningless

  * generating artificial data points through random replacement disregards the time sequence hence producing unrealistic values for the feature of interest (Figure 4)

​

​

​

​

​

​

​

​

​

​

​

​

​

​

​

Due to these insights, in this project, we also propose a generic XAI-technique for deep learning methods (DL) which preserves and exploits the natural time ordering of the data by introducing a family of so-called explainability (X-)functions. This concept bypasses severe identifiability issues, related among others to profane numerical optimization problems, and it promotes transparency by means of intuitively appealing input-output relations, ordered by time. 

In this second use case, we illustrate the generic concept based on financial time series and we derive explicit expressions for two specific X-functions for tracking potential non-linearity of the model and, by extension, for tracking non-stationarity of the data generating process. Our examples suggest that this natural extension of the original XAI-prospect, namely inferring a better understanding of the data from a better understanding of the model, might provide added value in a broad range of application fields, including risk-management and fraud detection.

![Bitcoin correctly_.png](/images/general/Bitcoin_correctly__9cca8a1d.png)

##### Figure 3. Bitcoin prices (original time ordering)

![Bitcoin shuffled.png](/images/general/Bitcoin_shuffled_77f44ef4.png)

##### Figure 4. Bitcoin prices original time ordering and shuffled values)