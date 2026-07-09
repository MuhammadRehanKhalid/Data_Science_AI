# ANOVA Tool Booklet

This booklet explains the main tests, when to use them, where they fit in the workflow, and how to interpret them.

## 1. One-way ANOVA

What it is: A test that compares the mean of one numeric response across one categorical factor with two or more groups.

When to use it: Use it when you have one treatment factor and one response variable.

How to use it: Put the factor in the first column and the response columns after it. The tool will treat every column after the first as a response.

What to look for: If the ANOVA p-value is below 0.05, at least one group mean is different.

## 2. Two-way ANOVA

What it is: A test for two factors and their interaction.

When to use it: Use it when you want to know whether factor A, factor B, or their combination changes the response.

How to use it: Place the two factor columns first, then the numeric response columns.

What to look for: A significant interaction means the effect of one factor depends on the other.

## 3. Three-way and Four-way ANOVA

What it is: Extensions of factorial ANOVA with three or four factors.

When to use it: Use these only when your experiment was designed with multiple interacting factors.

How to use it: Put the factor columns first, then the response columns.

What to look for: Check interaction terms carefully before interpreting main effects.

## 4. CRD

What it is: Completely Randomized Design. Treatments are assigned randomly with no block structure.

When to use it: Use it when every experimental unit is similar and there is no known blocking source.

How to use it: Put treatment first, then responses.

## 5. RCBD

What it is: Randomized Complete Block Design. Treatments are compared after accounting for block-to-block variation.

When to use it: Use it when you know there is nuisance variation across blocks such as location or time.

How to use it: Put treatment first, block second, then responses.

## 6. Split-plot designs

What it is: A design with a main-plot factor and a sub-plot factor, sometimes with deeper levels like split-split or strip-split.

When to use it: Use it when one factor is harder to change than the other.

How to use it: Keep the layout columns first in the exact order expected by the design, then the response columns.

What to look for: Main-plot effects often have larger experimental error than subplot effects.

## 7. Latin Square

What it is: A design that controls two blocking directions, usually row and column, while comparing treatments.

When to use it: Use it when row and column both create nuisance variation.

How to use it: Put row, column, treatment, then responses.

What to look for: The design assumes row and column effects are additive and balanced.

## 8. Post hoc tests

What they are: Follow-up pairwise comparisons done after a significant ANOVA.

Common choices:

- Tukey HSD: Best when you want all pairwise comparisons and group sizes are reasonably balanced.
- Tukey-Kramer: A version of Tukey that is better when group sizes are unbalanced but variances are still reasonably similar.
- Games-Howell: Best when variances are unequal or sample sizes are unbalanced.
- Duncan: A more liberal range test that is sometimes used for exploratory work when you want to detect more differences.
- Student-Newman-Keuls: A stepwise range test that is less conservative than Tukey and useful for ordered group comparisons.
- Holm: Good default when data are unbalanced or you want family-wise error control with more flexibility than Bonferroni.
- Bonferroni: Conservative, useful when you want strict error control.
- Sidak: Similar to Bonferroni but slightly less conservative.
- LSD: More liberal, useful only for exploratory work.
- Scheffe: Very conservative, useful when you want a strict test that stays safe even for complex contrasts.

How to choose: If the groups are balanced and variance looks similar, Tukey HSD is usually the best default. If the design is unbalanced but still fairly regular, Tukey-Kramer is a better fit. If variances are unequal, Games-Howell is usually the best choice. If you want a stricter safety-first option, choose Holm, Bonferroni, or Scheffe. If you are exploring patterns and not making a final claim, Duncan or LSD can be used, but they are more liberal.

## 9. Diagnostic plots

Residual histogram: Checks whether residuals look roughly normal.

Q-Q plot: Checks normality more directly.

Interaction plot: Helps identify interaction between factors.

Boxplot: Shows group spread and outliers.

Correlation heatmap: Useful when the dataset has several numeric variables.

## 10. Assumption checks

Shapiro-Wilk test: Checks residual normality.

Levene test: Checks equal variance across groups.

How to interpret: A p-value below 0.05 suggests the assumption may be violated and the result should be reviewed carefully.

## 11. Dummy data generator

What it is: A tool that creates example datasets with factor columns and response columns.

When to use it: Use it to learn the expected input format before running a real analysis.

How to use it: Choose the design from the menu, then save the generated CSV or Excel file.

What to look for: The generated file shows the exact column order the analysis functions expect.

## 12. Practical workflow

1. Generate a dummy dataset first if you want to learn the column structure.
2. Run the analysis on a real dataset.
3. Check the ANOVA table.
4. Review diagnostics and assumption checks.
5. Choose the post hoc test.
6. Review the post hoc table and the saved figures.

## 13. Output files

The tool saves:

- an Excel workbook with ANOVA tables and summaries
- a plot index sheet
- run summaries
- correlation tables when applicable
- figure files in an assets folder beside the workbook

## 14. Final note

ANOVA tells you whether differences exist. Post hoc tests tell you where those differences are. Diagnostics tell you whether the result is trustworthy.
