#!/usr/bin/env Rscript
# df <- read.csv("final_rr.csv")
# summary(df)
# 
# # # Random Chance Reciprocal Ranks
# # rand <- 1/sample(1:100, 100)
# # 
# # 
# # # Model Values
# tfidf <- df$Reciprocal_Rank[df$Model=="TF-IDF"]
# lda <- df$Reciprocal_Rank[df$Model=="LDA"]
# hdp <- df$Reciprocal_Rank[df$Model=="HDP-LDA"]
# at <- df$Reciprocal_Rank[df$Model=="Author-Topic"]
# llda <- df$Reciprocal_Rank[df$Model=="Labeled LDA"]

# # randomly sample 1000 for each model.
# # Model Values
# #tfidf <- sample(tfidf, 1000, replace=TRUE)
# #lda <- sample(lda, 1000, replace=TRUE)
# #hdp <- sample(hdp, 1000, replace=TRUE)
# #at <- sample(at, 1000, replace=TRUE)
# #llda <- sample(llda, 1000, replace=TRUE)
# 
# # means for each model
# course <- "Agile Planning for Software Products"
# mean(df$Reciprocal_Rank[df$Model=="TF-IDF" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="LDA" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="HDP-LDA" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="Author-Topic" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="Labeled LDA" & df$Course==course])
# 
# course <- "Client Needs and Software Requirements"
# mean(df$Reciprocal_Rank[df$Model=="TF-IDF" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="LDA" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="HDP-LDA" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="Author-Topic" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="Labeled LDA" & df$Course==course])
# 
# course <- "Design Patterns"
# mean(df$Reciprocal_Rank[df$Model=="TF-IDF" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="LDA" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="HDP-LDA" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="Author-Topic" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="Labeled LDA" & df$Course==course])
# 
# course <- "Introduction to Software Product Management"
# mean(df$Reciprocal_Rank[df$Model=="TF-IDF" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="LDA" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="HDP-LDA" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="Author-Topic" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="Labeled LDA" & df$Course==course])
# 
# course <- "Object Oriented Design"
# mean(df$Reciprocal_Rank[df$Model=="TF-IDF" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="LDA" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="HDP-LDA" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="Author-Topic" & df$Course==course])
# mean(df$Reciprocal_Rank[df$Model=="Labeled LDA" & df$Course==course])
# 
# mean(df$Reciprocal_Rank[df$Model=="TF-IDF"])
# mean(df$Reciprocal_Rank[df$Model=="LDA"])
# mean(df$Reciprocal_Rank[df$Model=="HDP-LDA"])
# mean(df$Reciprocal_Rank[df$Model=="Author-Topic"])
# mean(df$Reciprocal_Rank[df$Model=="Labeled LDA"])
# 
# # RQ1
# # Wilcoxon Rank Sum Test (Are the means different?)
# wilcox.test(rand, tfidf) # baseline
# wilcox.test(rand, at)
# wilcox.test(rand, hdp)
# wilcox.test(rand, lda)
# wilcox.test(rand, llda)
# 
# # Wilcoxon Rank Sum Tests against Baseline
# wilcox.test(tfidf, at)
# wilcox.test(tfidf, hdp)
# wilcox.test(tfidf, lda)
# wilcox.test(tfidf, llda)

# RQ2
# Are the means different for Labeled LDA and LDA/HDP-LDA?
df <- read.csv("final_rr.csv")
summary(df)
llda <- df$Reciprocal_Rank[df$Model=="Labeled LDA"]
hdp <- df$Reciprocal_Rank[df$Model=="HDP-LDA"]
lda <- df$Reciprocal_Rank[df$Model=="LDA"]

wilcox.test(llda, hdp, paired=TRUE)
wilcox.test(llda, lda, paired=TRUE)
