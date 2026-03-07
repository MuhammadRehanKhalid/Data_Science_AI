library(ggplot2)
library(readr)
library(dplyr)

df <- read.csv(file.choose())

categories <- df[,1:3]
data <- df[,4:ncol(df)]

num_vars <- ncol(data)/3

for(i in 1:num_vars){
  
  means <- data[,i*3-2]
  errors <- data[,i*3-1]
  letters <- data[,i*3]
  
  plot_data <- data.frame(
    variety = categories$variety,
    stress = categories$stress,
    treatment = categories$treatment,
    mean = means,
    error = errors,
    letters = letters
  )
  
  plot_data$category <- paste(plot_data$variety, plot_data$stress, sep="_")
  
  p <- ggplot(plot_data, aes(x=category, y=mean, fill=treatment)) +
    
    geom_bar(
      stat="identity",
      position=position_dodge(0.8),
      color="black",
      width=0.7
    ) +
    
    geom_errorbar(
      aes(ymin=mean-error, ymax=mean+error),
      width=0.2,
      position=position_dodge(0.8)
    ) +
    
    geom_text(
      aes(label=letters, y=mean+error),
      position=position_dodge(0.8),
      vjust=-0.5
    ) +
    
    scale_fill_brewer(palette="Set2") +
    
    theme_classic() +
    
    labs(
      x="Variety × Stress",
      y=colnames(data)[i*3-2],
      fill="Treatment"
    )
  
  print(p)
}
