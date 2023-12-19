#--------Saving Method---------------------------#
p<- heatmaply(
  percentize(mydata)[1:10,],
  seriate = "GW"
)
ggsave("fkoff.png",width = 6, height = 4, units = "in", dpi = 1200)
p
dev.off()
library(heatmaply)
#----------------------packages-------------------#
webshot::install_phantomjs()
library("microbenchmark")
install.packages("microbenchmark")
library("heatmaply")
library("pheatmap")
library(RColorBrewer)
par(mar=c(3,4,2,2))
display.brewer.all()
if (!requireNamespace("BiocManager", quietly = TRUE))
  install.packages("BiocManager")

# install and load package
BiocManager::install("DESeq")
library("DESeq")

if you cant install DESeq, I have hosted the file at https://davetang.org/file/TagSeqExample.tab
example_file <- "https://davetang.org/file/TagSeqExample.tab"


#-----------------------------pheatmap-------------#
library("factoextra")
my_data <- read.csv(file.choose())
data <- as.matrix(my_data)

pheatmap(LC)
pheatmap(LC, scale="column", col = cm.colors(256))
pheatmap(LC, scale="column", display_numbers = T, col = terrain.colors(256))


##---------------------------------display_numbers = T----------------
library(RColorBrewer)
library(heatmaply)
coul <- colorRampPalette(brewer.pal(8, "Set1"))(25)
pheatmap(data, scale="column", col = coul, display_numbers = T, dendogram = "none")

my_data <- read.csv(file.choose())
data <- expand.grid(my_data)
ggplot(my_data, aes(X, Y, fill= Z)) +
  geom_tile()

# The default of heatmaply:
heatmaply(
  percentize(my_data)[1:10, ],
  seriate = "OLO"
)
# Similar to OLO but less optimal (since it is a heuristic)
heatmaply(
  percentize(my_data)[1:10, ],
  seriate = "GW"
)
# the default by gplots::heatmaply.2
heatmaply(
  percentize(my_data)[1:10, ],
  seriate = "mean"
)
# the default output from hclust
heatmaply(
  percentize(my_data)[1:10, ],
  seriate = "none"
)

#scale_fill_gradient_fun:
heatmaply(
  my_data,
  scale_fill_gradient_fun = ggplot2::scale_fill_gradient2(
    low = "red",
    high = "Black",
    midpoint = 25,
    limits = c(0, 50)
  )
)
#changing color for heat maps
heatmaply(
  percentize(my_data)[1:10],
  colors = heat.colors(100)
)
my_palette<-PurplesANDYellow(50)
heatmaply(data, dendroram="none",
          scale_fill_gradient_fun = ggplot2::scale_fill_gradient2(
            low = "magenta", mid="yellow",high = "purple", midpoint = 0,
            limits = c(-0.5, .5)))
# Example for using RowSideColors
my_data <- read.csv(file.choose())
x  <- as.matrix(my_data)
rc <- colorspace::rainbow_hcl(nrow(x))
library("viridis")
heatmap(
  x,
  trace = "none",
  col = viridis(100),
  RowSideColors = rc,
  key = FALSE,
)
heatmap.2(
  x,
  trace = "none",
  col = viridis(100),
  RowSideColors = rc,
  key = FALSE
)
heatmaply(my_data,
          seriate = "mean",
          row_dend_left = TRUE,
          plot_method = "plotly"
)

heat_map_save(
  save_as,
  width = 7,
  height = 7,
  units = "in",
  res = 300,
  multiple = FALSE,
  layout = NULL,
)
#----------------------Save Heatmap---------------
if (FALSE) {
  heat_map_save("Heatmap.png",
                height = 7,
                width = 5)}
library("gplots")
#group Colors (Not Worked)
my_data <- as.numeric(as.factor(substr(rownames(my_data), 1 , 1)))
colSide <- brewer.pal(9, "Set1")[my_data]
colMain <- colorRampPalette(brewer.pal(8, "Set2"))(25)
pheatmap(data, Colv = NA, Rowv = NA, scale="column" , RowSideColors=colSide, col=colMain   )

# Add classic arguments like main title and axis title
pheatmap(data, Colv = NA, Rowv = NA, scale="column", col = coul, xlab="plant parameters", ylab="Columns", main="heatmap")

# Custom x and y labels with cexRow and labRow (col respectively)
pheatmap(data, scale="column", cexRow=1.5, labRow=paste("new_", rownames(data),sep=""), col= colorRampPalette(brewer.pal(8, "Set3"))(25))
#Use  different color palate for upper line

install.packages("latticeExtra")
library(ggplot2)
install.packages("hrbrthemes")
library(hrbrthemes)
install.packages("plotly")
library(plotly)



#3D Not worked
install.packages("latticeExtra")
library(latticeExtra)
# A function generating colors
cols<-function(n) {
  colorRampPalette(c("#FFC0CB", "#CC0000"))(20)                                 # 20 distinct colors
}

#heatmap by ggplot
my_data <- read.csv(file.choose())
data <- as.matrix(my_data)
ggplot(data)
data <- expand.grid(X=x, Y=y)
data$Z <- runif(400, 0, 5)

# Heatmap
ggplot(data, aes(X, Y, fill= Z)) +
  geom_tile()
ggplotly

#Correltion heatmap
heatmaply_cor(
  cor(my_data),
  xlab = "Features",
  ylab = "Features",
  k_col = 2,
  k_row = 2
)

r <- cor(my_data)
## We use this function to calculate a matrix of p-values from correlation tests
## https://stackoverflow.com/a/13112337/4747043
#-----------------------
cor.test.p <- function(x){
  FUN <- function(x, y) cor.test(x, y)[["p.value"]]
  z <- outer(
    colnames(x),
    colnames(x),
    Vectorize(function(i,j) FUN(x[,i], x[,j]))
  )
  dimnames(z) <- list(colnames(x), colnames(x))
  z
}
p <- cor.test.p(my_data)

heatmaply_cor(p,
              node_type = "scatter",
              point_size_mat = -log10(p),
              point_size_name = "-log10(p-value)",
              label_names = c("x", "y", "Correlation")
)
heatmaply(
  percentize(my_data1),
  xlab = "Features",
  ylab = "Cars",
  main = "Data transformation using 'percentize'"
)
heatmaply(
  my_data,
  cellnote = my_data
)
library(plotly)
dir.create("folder")
heatmaply(my_data, file = "folder/heatmaply_plot.html")
browseURL("folder/heatmaply_plot.html")
webshot::install_phantomjs()
heatmaply(my_data, file = "my_data.pdf")
#----------------------Heatmap----------------

library("heatmap")

library(RColorBrewer)
par(mar=c(3,4,2,2))
display.brewer.all()

library("factoextra")
my_data <- read.csv(file.choose())
data <- as.matrix(my_data)

heatmap(data)
heatmap(data, scale="column", col = cm.colors(100))
redgreen <- c("red", "green")
pal <- colorRampPalette(redgreen)(100)
pal <- colorRampPalette(brewer.pal(11, "RdYlGn"))(100)

heatmap(data, scale="column", col = terrain.colors("RdBu"))
levelplot(data, col.regions=heat.colors)

library(RColorBrewer)
coul <- colorRampPalette(brewer.pal(8, "YlGnBu"))(25)
heatmap(data, scale="column", col = coul)

my_data <- read.csv(file.choose())
data <- expand.grid(my_data)
ggplot(my_data, aes(X, Y, fill= Z)) +
  geom_tile()

# The default of heatmaply:
heatmaply(
  percentize(my_data)[1:10, ],
  seriate = "OLO"
)
# Similar to OLO but less optimal (since it is a heuristic)

p<- heatmaply(
  percentize(LC)[1:10,],
  seriate = "GW"
)
ggsave("barplotRehan.pdf",width = 6, height = 4, units = "in", dpi = 1200)
p
dev.off()

tiff('Barplotly.png', units="in", width=10, height=6, dpi=300, compression = 'lzw')
Sys.setenv(R_GSCMD="gs9561w64.exe")


# the default by gplots::heatmaply.2
heatmaply(
  percentize(my_data)[1:10, ],
  seriate = "mean"
)
# the default output from hclust
heatmaply(
  percentize(my_data)[1:10, ],
  seriate = "none"
)

#scale_fill_gradient_fun:
heatmaply(
  my_data,
  scale_fill_gradient_fun = ggplot2::scale_fill_gradient2(
    low = "blue",
    high = "red",
    midpoint = 250,
    limits = c(0, 500)
  )
)
#changing color for heat maps
heatmaply(
  percentize(my_data)[1:10],
  colors = heat.colors(100)
)
my_palette<-PurplesANDYellow(50)
heatmaply(data, dendroram="none",
          scale_fill_gradient_fun = ggplot2::scale_fill_gradient2(
            low = "magenta", mid="black",high = "yellow", midpoint = 0,
            limits = c(-2, 2)))
# Example for using RowSideColors
my_data <- read.csv(file.choose())
x  <- as.matrix(my_data)
rc <- colorspace::rainbow_hcl(nrow(x))
library("viridis")
heatmap(
  x,
  trace = "none",
  col = viridis(100),
  RowSideColors = rc,
  key = FALSE,
)
heatmap.2(
  x,
  trace = "none",
  col = viridis(100),
  RowSideColors = rc,
  key = FALSE
)
heatmaply(my_data,
          seriate = "mean",
          row_dend_left = TRUE,
          plot_method = "plotly"
)

heat_map_save(
  save_as,
  width = 7,
  height = 7,
  units = "in",
  res = 300,
  multiple = FALSE,
  layout = NULL,
)
# Save Heatmap

install.packages("viridisLite")

#----------heatmap ggplot----------


