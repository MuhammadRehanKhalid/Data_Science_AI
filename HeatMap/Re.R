# Load the necessary libraries
library(dplyr)
library(tidyr)

# Define the URL of the COVID-19 pandemic Wiki page
url <- "https://en.wikipedia.org/wiki/COVID-19_pandemic"

# Send a GET request to the URL to get the page content
response <- GET(url)

# Extract the content of the response as text
content <- content(response, as = "text")

# Use rvest to parse the HTML content
html <- read_html(content)

# Extract the COVID-19 testing data table using rvest and XPath selectors
table <- html %>%
  html_nodes(xpath = '//*[@id="covid19-testing"]//table') %>%
  html_table()

# # Convert the table to a data frame and clean the data
# covid_df <- as.data.frame(table) %>%
#   filter(Country != "") %>%
#   mutate(`Total tested` = gsub("\\[.*?\\]", "", `Total tested`),
#          `Total tested` = as.numeric(gsub(",", "", `Total tested`)),
#          Positive = as.numeric(gsub("%", "", Positive))/100,
#          Death = as.numeric(gsub(",", "", Death)),
#          Test = as.numeric(gsub(",", "", Test)),
#          Test.per.M = as.numeric(gsub(",", "", `Test per M`)),
#          Country = gsub("\\[[^\\]]*\\]", "", Country)) %>%
#   select(Country, `Total tested`, Positive, Death, Test, `Test per M`) %>%
#   arrange(desc(Positive)) %>%
#   mutate(rank = row_number())
# pre-process the extracted data frame
covid_df <- covid_df %>%
  select(Country, `Total tested`, Positive, Deaths, Tests.per.million) %>%
  mutate(`Total tested` = gsub("\\[.*?\\]", "", `Total tested`)) %>%
  mutate_at(vars(`Total tested`:Positive), list(~as.numeric(gsub(",", "", .)))) %>%
  drop_na() %>%
  arrange(desc(Positive)) %>%
  mutate(rank = row_number())

# export the data frame to a CSV file
write.csv(covid_df, "covid_testing_data.csv", row.names = FALSE)

# Export the data frame to a CSV file
write.csv(covid_df, "covid_testing_data.csv", row.names = FALSE)

# Get a subset of the extracted data frame for the United States
us_data <- covid_df %>% filter(Country == "United States")

# Print the subset to the console
print(us_data)
