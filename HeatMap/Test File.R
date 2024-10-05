install.packages("ggpubr","kassambara")
library(ggpubr)
#First Code  is For PCA Correlation.
library(factoextra)
my_data<- read.csv(file.choose())
jpeg ("rehan2121212.jpeg", width = 10, height = 10, units = "in", res = 300)
res.pca<- prcomp(my_data[-1,],scale=TRUE)
fviz_eig (res.pca)
#diff color

fviz_pca_ind(res.pca,
             col.ind = "cos2",
             gradient.cols = c("red", "purple", "green"),
             repel = TRUE)
#to calculate the individual PCA fro treatment/genotype/variety
fviz_pca_ind(res.pca,
             col.ind="cos2", #color by quality
             gradient.cols = c("red", "blue", "green", "yellow"),
             repel= TRUE #avoid overlapping
)
#to calculate PCA of PARAMETER
fviz_pca_var(res.pca,
             col.var = "contrib", #color  by contribution
             gradient.cols = c("red", "black", "green", "blue"),
             repel = TRUE
)
dev.off()
#Color #00AFBB", "#E7B800", "#FC4E07
#FFCC00", "#CC9933", "#660033", "#330033



install.packages("extrafont")
library(extrafont)
font_import() # this gets fonts installed anywhere on your computer, most commonly from MS Office install fonts. It takes a LONG while.
fig <- image_graph(width = 400, height = 400, res = 3000)
ggplot2::qplot(mpg, wt, data = mtcars, colour = cyl)
dev.off()
y




#1#co-relation plot 1
#Method “circle”, “square”, “ellipse”, “number”, “shade”, “color”, “pie”
library(corrplot)
m <- read.csv(file.choose())
M=cor(m)
corrplot(M,method = "pie")
corrplot(M,method = "pie", addCoef.col = "black",col = COL2("PRGn"))
corrplot(M,method = "pie", addCoef.col = "black",col = COL2("PiYG"))

library(corrplot)
M=cor(PCA)
corrplot(M, method = 'pie', order = 'AOE', addCoef.col = 'black', tl.pos = 'lt',
         cl.pos = 'b', col = COL2('RdBu'))
#should be one of “RdBu”, “BrBG”, “PiYG”, “PRGn”, “PuOr”, “RdYlBu”

#2#for triangle form
library(corrplot)
M=cor(Correlation)
corrplot(M,method = "pie", order = "FPC", type = "upper", diag = FALSE,col = COL2('RdYlBu'))
#2#for triangle form with Numbers
M=cor(Correlation)
corrplot(M,method = "pie", order = "hclust", type = "upper", diag = FALSE,addCoef.col = "black",col = COL2("PuOr"))

--------------------------------------------------------------
  #3#co-relation plot 2
  #order 'AOE', 'FPC', 'hclust', 'alphabet'
  library(corrplot)
M=cor(Correlation)
corrplot(M,order="hclust")
#for drwaing boxes round
corrplot(M,order="hclust", addrect = 2)

library(corrplot)
M=cor(Correlation)
corrplot(M, method = 'pie', order = 'alphabet')
corrplot(M, method = 'pie', order = 'alphabet',addCoef.col = "black",col = COL2("PuOr"))

#corrplot.mixed fro upper and lower different things
#1
library(corrplot)
M=cor(Correlation)
corrplot.mixed(M,order="AOE")
corrplot.mixed(M,order="AOE", addCoef.col = 'blue')
#2 lower and upper triangle different styles
library(corrplot)
M=cor(PCA)
corrplot.mixed(M,lower = "pie", upper = "shade", order= "hclust", tl.pos = 'lt' )
#Values
M=cor(Correlation)
corrplot.mixed(M,lower = "pie", upper = "shade", order= "hclust", tl.pos = 'lt',addCoef.col = "black")

#4# bottom color legend, diagonal text legend, rotate text label
library(corrplot)
M=cor(DATAX)
corrplot(M, order = 'AOE', cl.pos = 'b', tl.pos = 'd',
         col = COL2('PRGn'), diag = FALSE)

library(corrplot)
M=cor(DATAX)
corrplot(M, order = 'AOE', addCoef.col = 'black', tl.pos = 'd',
         cl.pos = 'n', col = COL2('PiYG'))

## remove color legend, text legend and principal diagonal glyph
library(corrplot)
M=cor(DATAX)
corrplot(M, order = 'AOE', cl.pos = 'n', tl.pos = 'n',
         col = c('white', 'black'), bg = 'gold2')
## add all p-values
library(corrplot)
M=cor(DATAX)
corrplot(M, p.mat = testRes$p, insig = 'p-value', sig.level = 1.0)
M=cor(DATAX)
corrplot(M, p.mat = testRes$p, method = 'color', diag = FALSE, type = 'upper',
         sig.level = c(0.001, 0.01, 0.05), pch.cex = 0.9,
         insig = 'label_sig', pch.col = 'grey20', order = 'AOE')
------------------------------------------------------------------------
  #chat.correlation
  # install.packages("Performance Analytics")
  install.packages("PerformanceAnalytics")
library(PerformanceAnalytics)

chart.Correlation(M, histogram = TRUE, method = "pearson")

#psych relation
install.packages("psych")
library(psych)

pairs.panels(my_data,
             smooth = TRUE,      # If TRUE, draws loess smooths
             scale = FALSE,      # If TRUE, scales the correlation text font
             density = TRUE,     # If TRUE, adds density plots and histograms
             ellipses = TRUE,    # If TRUE, draws ellipses
             method = "pearson", # Correlation method (also "spearman" or "kendall")
             pch = 21,           # pch symbol
             lm = FALSE,         # If TRUE, plots linear fit rather than the LOESS (smoothed) fit
             cor = TRUE,         # If TRUE, reports correlations
             jiggle = FALSE,     # If TRUE, data points are jittered
             factor = 2,         # Jittering factor
             hist.col = 4,       # Histograms color
             stars = TRUE,       # If TRUE, adds significance level with stars
             ci = TRUE)          # If TRUE, adds confidence intervals

my_packages<-as.data.frame(installed.packages()[,c(1,3:4)])
my_packages<-my_packages[is.na(my_packages$Priority),1:2, drop=FALSE]
rownames(my_packages)<-NULL
head(my_packages)
View(my_packages)
install.packages("ggcorrplot")
install.packages("chron")
install.packages("gridGraphics")
library(gridGraphics)
install.packages("lattice")
install.packages("plotrix")
install.packages("graphics")
install.packages("latticeExtra")
library(ggplot2)
install.packages("factoextra")
install.packages("FactoMineR")
install.packages("hrbrthemes")
library(hrbrthemes)
install.packages("plotly")
library(plotly)
install.packages("heatmaply")
library(heatmaply)
install.packages("pheaheatmap")

install.packages("pheatmap")
install.packages("reshape2")
library(heatmaply)
install.packages("heatmap.2")
webshot::install_phantomjs()
heatmaply(mtcars, file = "heatmaply_plot.pdf")
library(viridis)
library(chron)
library(lattice)
library(plotrix)
library(graphics)
setwd("D:\\Study and Extras\\R Files Projects")
bitmap("rehan.tiff", height = 4, width = 4, units = 'in', type="tifflzw", res=300)
dev.off()
par(mfrow = c(1,1))
jpeg("image.tiff",
     width = 6, height = 6, units = "in", res = 600)
dev.off()

---------------------------------------------------
  # leave blank on non-significant coefficient
  # add significant correlation coefficients
library(corrplot)
M=cor(DATAX)
corrplot(M, p.mat = Correlation$P, method = 'circle', type = 'lower', insig='blank',
         addCoef.col ='black', number.cex = 0.8, order = 'AOE', diag=FALSE)
# add p-values on no significant coefficients
corrplot(M, p.mat = M, insig = 'p-value')

# add significant level stars
corrplot(M, p.mat = M, method = 'color', diag = FALSE, type = 'upper',
         sig.level = c(0.001, 0.01, 0.05), pch.cex = 0.9,
         insig = 'label_sig', pch.col = 'grey20', order = 'AOE')



###[1] "Oceanic - Eighties"
download.file("https://git.io/rstudio-theme-oceanic-eighties", oceanic_theme)
rstudioapi::addTheme(oceanic_theme, apply = TRUE)
## "Yule - Eighties"
eramyule_theme <- fs::path_temp("Yule-RStudio", ext = "rstheme")
download.file("https://git.io/yule-rstudio", yule_theme)
rstudioapi::addTheme(yule_theme, apply = TRUE)
Night Owlish
rstudioapi::addTheme("https://raw.githubusercontent.com/batpigandme/night-owlish/master/rstheme/night-owlish.rstheme", apply = TRUE)
Syntnwave65
rstudioapi::addTheme("https://raw.githubusercontent.com/jnolis/synthwave85/master/Synthwave85.rstheme", TRUE, TRUE, FALSE)

M<-read.csv(file.choose())
M = as.matrix(M,"16,45")
corrplot(M, method = 'color', diag = TRUE, type = 'upper',
sig.level = c(0.001, 0.01, 0.05), pch.cex = 0.9,
insig = 'label_sig', pch.col = 'grey20', order = 'AOE')


setwd("D:\\Study and Extras\\R Files Projects")
lapply(.packages(all.available = TRUE), function(xx)library(xx,character.only = TRUE))
rstudioapi::addTheme("https://raw.githubusercontent.com/jnolis/synthwave85/master/Synthwave85.rstheme", TRUE, TRUE, FALSE)
install.packages("rstudioapi")

rstudioapi::addTheme("https://raw.githubusercontent.com/dracula/rstudio/master/dracula.rstheme", apply = TRUE)
remotes::install_github("anthonynorth/rscodeio")
