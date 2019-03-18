#!/usr/bin/env Rscript
df <- read.csv("final_mrr.csv")
summary(df)

# Random Chance Reciprocal Ranks
rand <- 1/sample(1:100, 100)

# Model Values
tfidf <- df$Reciprocal_Rank[df$Model=="TF-IDF"]
at <- df$Reciprocal_Rank[df$Model=="Author-Topic"]
hdp <- df$Reciprocal_Rank[df$Model=="HDP-LDA"]
lda <- df$Reciprocal_Rank[df$Model=="LDA"]
llda <- df$Reciprocal_Rank[df$Model=="Labeled LDA"]

# means for each model
mean(tfidf)
mean(at)
mean(hdp)
mean(lda)
mean(llda)

# RQ1
# Wilcoxon Rank Sum Test (Are the means different?)
wilcox.test(rand, tfidf) # baseline
wilcox.test(rand, at)
wilcox.test(rand, hdp)
wilcox.test(rand, lda)
wilcox.test(rand, llda)

# Wilcoxon Rank Sum Tests against Baseline
wilcox.test(tfidf, at)
wilcox.test(tfidf, hdp)
wilcox.test(tfidf, lda)
wilcox.test(tfidf, llda)

# RQ2
# Are the means different for Labeled LDA and LDA/HDP-LDA?
wilcox.test(llda, hdp) # fail to reject
wilcox.test(llda, lda) # reject
# guess we need to run this for each course...
course <- "Agile Planning for Software Products"
llda <- df$Reciprocal_Rank[df$Model=="Labeled LDA" & df$Course==course]
hdp <- df$Reciprocal_Rank[df$Model=="HDP-LDA" & df$Course==course]
lda <- df$Reciprocal_Rank[df$Model=="LDA" & df$Course==course]
wilcox.test(llda, hdp) # fail to reject
wilcox.test(llda, lda) # fail to reject

course <- "Client Needs and Software Requirements"
llda <- df$Reciprocal_Rank[df$Model=="Labeled LDA" & df$Course==course]
hdp <- df$Reciprocal_Rank[df$Model=="HDP-LDA" & df$Course==course]
lda <- df$Reciprocal_Rank[df$Model=="LDA" & df$Course==course]
wilcox.test(llda, hdp) # reject
wilcox.test(llda, lda) # fail to reject

course <- "Design Patterns"
llda <- df$Reciprocal_Rank[df$Model=="Labeled LDA" & df$Course==course]
hdp <- df$Reciprocal_Rank[df$Model=="HDP-LDA" & df$Course==course]
lda <- df$Reciprocal_Rank[df$Model=="LDA" & df$Course==course]
wilcox.test(llda, hdp) # reject
wilcox.test(llda, lda) # fail to reject

course <- "Introduction to Software Product Management"
llda <- df$Reciprocal_Rank[df$Model=="Labeled LDA" & df$Course==course]
hdp <- df$Reciprocal_Rank[df$Model=="HDP-LDA" & df$Course==course]
lda <- df$Reciprocal_Rank[df$Model=="LDA" & df$Course==course]
wilcox.test(llda, hdp) # fail to reject
wilcox.test(llda, lda) # reject

course <- "Object Oriented Design"
llda <- df$Reciprocal_Rank[df$Model=="Labeled LDA" & df$Course==course]
hdp <- df$Reciprocal_Rank[df$Model=="HDP-LDA" & df$Course==course]
lda <- df$Reciprocal_Rank[df$Model=="LDA" & df$Course==course]
wilcox.test(llda, hdp) # reject
wilcox.test(llda, lda) # fail to reject
