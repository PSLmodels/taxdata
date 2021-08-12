
This memorandum documents the procedures, programs and results from performing a constrained statistical match between the 2004 SOI Public Use File (PUF) and the March 2005 Current Population Survey (CPS). First, we provide an overview of statistical matching and how this relates to the specific challenges of combining information from the SOI and CPS. Second, we describe the SAS programs we developed in the course of implementing the match. Finally, we present the results of the match performed in November 2009.


# Overview of Statistical Matching

In the standard statistical matching framework, one has observations from two data sets (File A and File B) on a set of common variables (X-variables). Additionally, records from File A contain information on another set of variables (Y-Variables) that are not available on File B. Similarly, File B contains information on a third set of variables (Z- Variables) that are not available on File A. Statistical matching involves creating a new data set (File C) containing information on X, Y and Z.

Statistically matched data sets are used most extensively as inputs to microsimulation models [Cohen(1991)] where the impacts of a policy change are examined across various subgroups of the population where data limitations are often severe. For example, the SOI contains a great deal of detail on taxable income sources and certain expenditures (e.g., health-related costs and home mortgage interest expenses for those taxpayers who itemize) but very little information on transfer payments (e.g., food stamps and AFDC), employment-related fringe benefits (health insurance) and family composition. An ideal data set would combine information from both sources.

From an historical perspective, the first statistically matched data file for use in microsimulation was created for tax policy analysis [Okner (1972)] and combined the SOI with the Survey of Economic Opportunity (SEO). An up-to-date survey of statistical matching methods and a description of how they are implemented in applied work is Cohen (1992).

In this project, we update and extend earlier SOI-CPS matches. We have three goals:
* Construct a statistically matched data set combining the 2004 SOI with the March 2005 CPS that can be a reliable input to tax policy analysis.
* Introduce methods that ease the computational burden of (constrained) statistical matching, are straightforward to implement and have desirable statistical properties.
* Provide documented computer algorithms and source code so the matches can be updated on a regular basis with minimal effort.

## Constrained vs. Unconstrained Statistical Matching


Most authors distinguish between two types of statistical matching methods based on how the records in both files are combined. In constrained matching, all of the records in both data files are represented in the final matched data set (File C). In order to achieve this result, there are limits placed on the number of times a particular record in File B can be matched to a record in File A. Records on both files are often "split", or used more than once, in a constrained match and the limits are enforced by making sure that the population weight attached to each record is "used-up" in the match. A necessary condition for performing a constrained match, but one that is difficult to meet in practice, is that both input files have the same weighted population totals.[^footnote1]

Unconstrained matching does not require that all of the records in File B be used up the match, but it is almost always the case that each record in the Host file appears in the final matched file. In practice, certain limits are usually imposed on the number of times a Donor (File B) record can be used in an unconstrained match to ensure that the (weighted) distributions of the Z-variables "brought over" in the match are closely aligned with the distributions on the original file.

Experience suggests that, of the two, unconstrained matching is the most popular choice for constructing microsimulation data sets since it makes fewer demands on system resources. On the other hand, there are advantages to be gained in constrained matching and with the advent of more powerful computers, cheaper memory and faster numerical algorithms, this method has become increasingly more common.

A common criticism of statistical matching is that it relies on rather strong assumptions about the relationship between the Y- and Z-variables [Kadane (1978)]. In particular, an implicit assumption in statistical matching is that they are independent (or uncorrelated if normality is assumed) given an observation of X-variables. This Conditional Independence Assumption (CIA) is often violated in practice and has caused researchers to investigate alternative methods of combining data sets [Rubin (1986); Armstrong (1989); Singh et. al. (1993)].

### *Unconstrained Matching*

Unconstrained statistical matching is probably the most popular type of matching being done today, at least with regard to microsimulation applications. Various approaches to unconstrained statistical matching are comparatively simple to implement, cost effective, easy to replicate and update, and intuitive.

In unconstrained matching, one seeks a record in File B that resembles or is in some sense “close” to a record in File A. This presumes some sort of metric or distance function is introduced. One commonly used metric, the Euclidean distance normalized by the standard deviation, appears frequently in the literature.

Let $X^A_{i1}$, $X^A_{i2}$, ..... $X^A_{in}$ denote a set of X-variables from record i in File A used to construct the distance function and $X^B_{j1}$, $X^B_{j2}$, ......, $X^B_{jn}$ be similar values of the <u>same</u> variables from record j in File B. Then the distance function is:
$$
d_{ij} = \left[\sum_{k}\left(\left(X^A_{ik}-X^B_{jk} / \sigma_k^2 \right)\right) \right]^{\frac{1}{2}}
$$
where $\sigma_k$ is the standard deviation of the kth X-variable in File A. It should be emphasized that the choice of an appropriate distance function can have important consequences for the integrity of the matched dataset [Paass(1985)].

Minimum distance matching (or “nearest neighbor” matching) was probably the first large-scale statistical matching method to be performed for use in a microsimulation environment [see Okner (1972)]. It’s also very easy to describe: for each record in File A, select the record in File B that is “closest” in a minimum distance sense. Like all unconstrained matches, minimum distance matching suffers from the fact that the marginal distributions of the Z-variables in the matched file could be quite different than on the original file and it is important to check the validity of the results. In a sense, most unconstrained methods represent refinements of this procedure [Armstrong (1989)].

### *Constrained Matching*

Statistically matched data sets constructed by constrained matching have nice properties: means and variances of the X, Y and Z variables in both input files are preserved as a direct consequence of the constraints imposed on the weights occurring in the final matched data set. One drawback of constrained matching, however, is that records may end up being matched with an unacceptably large distance between the X-variables. Constrained matching can also make very large demands on system resources. Barr and Turner (1979, 1980) provide a concise and useful summary of the technical details of constrained matching as well as a discussion of many of the practical problems one encounters in applied work.

In some implementations of fully constrained matching, one seeks to minimize the overall distance between records in File A and File B that appear in File C. Mathematically, one attempts to minimize:

$$
\sum_{i}\sum_{j} (d_{ij} * w_{ij})
$$
$$
\text{subject to: } \sum_{j} w_{ij} = a_i \text{ and } \sum_i w_{ij} = b_j
$$

where $a_i$ and $b_j$ are the original weights on File A and File B and $w_{ij}$ is the weight on File C obtained from matching the ith record on File A with the jth record on File B.[^footnote2] This problem has the structure of the transportation (or transshipment) problem in network optimization theory. (Think of the records in File A as the "factories" (sources) and the records in File B as the "warehouses" (sinks). The constraints ensure all of the product (e.g., the weights) gets shipped. Bertsekas (1991) contains a nice discussion of the transportation problem. Figure 1 shows schematically how record are combined in constrained statistical matching.

```{figure} figure1.png
---
height: 150px
name: directive-fig
---
Constrained Statistical Matching
```


Paass (1985) and Rodgers (1984) favor constrained matching over unconstrained, nearest-neighbor methods. They believe that the additional cost (in terms of resources) are justified and outweigh the possibility of error introduced by unconstrained matching.

### *Methodological Approach*
The approach we will implement for this project is referred to as fully constrained, predictive mean matching. Constraining the match to utilize all records on both files ensures that the marginal distributions of the Z-variables will be carried over onto the matched file.[^footnote3] This is a desirable result. Predictive mean matching is a technique by which the correlation between the X-, Y- and Z- variables is exploited in the match by using predicted values to determine the nearest-neighbor match.[^footnote5] Predictive mean matching performs well in practice [Armstrong (1989)] and is straightforward to implement.

We employ an extensive partitioning scheme on both input files to create equivalence classes where matches are only allowed within these classes. This procedure has the effect of narrowing the distance between records and allows for a tighter fit across the two data sets.[^footnote5] A more detailed description of the procedure is included as an attachment to this document.

# Results

In the first step of the match, we construct tax units from the CPS file. We impose the constraint that there should be at least one tax unit in every household. We combine information from the household, family and person records to construct each tax unit. A summary of the March 2005 CPS records is contained in Tables 1A through 1D in Appendix A.

Once person records in each household are combined to form tax units, we make an initial determination of whether that tax unit is legally required to file a federal income tax return based on filing thresholds in place for the Tax Year 2004, the most recent year for which a Public Use File (PUF) is available.[^footnote6] In this match, we used a slightly different methodology for choosing tax filers. In prior matches, we adjusted filing thresholds to get the approximate number of returns in broad, taxpayer classes. We modified this approach in the current match to more closely approximate what is done in the Tax Policy Center’s (TPC) model. That is, we randomly selected tax units that were initially determined to not be required to file a tax return and reclassified them as a tax filer. We did this across all taxpayer subgroups. Weighted and unweighted counts of CPS tax units are shown in Tables 2A through 2D. Similar counts from the 2004 PUF are shown in Tables 3A and 3B.

In the next step, we partition both files across several dimensions to ensure that matches are not done outside of a particular cell. We construct 18 cells to reflect: (i) dependency status, (ii) marital status, (iii) age, and (iv) the number of dependents. Our partition and the corresponding weighted and unweighted record counts are shown in Table 4.

In our third step, we construct a distance metric by regressing taxable income on the PUF to a collection of independent variables that we believe are related to taxable income.

These variables include: a indicator if the taxpayer is 65 years of age or older, various income sources (e.g., wages, interest, dividends), the share of total income attributable to capital and labor, respectively, and indicator variables if the taxpayer received either wages or self-employed income. We estimate 18 separate regressions, one for each cell, and construct fitted values on the CPS using the same set of predictor variables. The distance between records on the CPS and the PUF is then calculated as the square root of the (squared) difference between the fitted values. The methodology for matching records between the files is described in Appendix B. The regression coefficients and other measures of goodness-of-fit are shown in Tables C1 through C18 in Appendix C.

In our final step, we evaluate the match by comparing means and standard errors for CPS variables added to the PUF on both the original CPS file and the final Match File. These results are reported in Table 5. The final column in Table 5 is a t-test to examine differences in means between the two files. (The null hypothesis is that the means are equal in the two files.) These results should be interpreted with caution as the values of the standard errors on the Match File are not adjusted for sample design.

# Differences Between PwC Match and TPC Match

We are aware of only two differences in the methodology reported here and the methodology described in TPC’s documentation.[^footnote7]

<u>Partitioning</u>. TPC expanded the number of cells in the partition to include indicators if the tax unit had self-employed income or income from capital. This resulted in a much larger number of cells (49) in the TPC match. One drawback of expanding the number of cells in this way is that certain cells become “unbalanced” and in the process of adjusting the weights on the CPS file to match the weights on the PUF (this is necessary to perform a constrained statistical match) certain CPS variables might not be indicative of their true values.[^footnote8] The trade-off between more cells and a potentially large adjustment is more an art than a science. In any event, adding more cells to the PwC match is a simple extension.

<u>Non-filers</u>. TPC relied on a series of probit equations reported by Cilke (1998)[^footnote9] to identify potential CPS tax units that were not legally required to file a federal income tax return but did. Cilke related the probability of filing a return (given that the taxpayer was not legally required to do so) as a function of income and numerous demographic variables. These probabilities were then adjusted to approximate control totals for certain taxpayer groups. Incorporating this methodology, while somewhat time-consuming, is straightforward. Because this would have necessitated rerunning the match to include many more demographic variables, we approximated this approach by randomly selecting non-filers in specific taxpayer subgroups and re-classified them as filers so as to match SOI totals in that subgroup.

# Description of the SAS Programs

In this project, we perform a constrained statistical match between the 2004 SOI Public Use File (PUF) and March 2005 Current Population Survey (CPS).[^footnote10] The PUF plays the role of the Host file while the CPS is the Donor. Before we can perform the match, however, we must make sure both files represent the same observational unit. Because the PUF is a sample of tax returns, an important early step in this process is to construct tax returns, or tax units, from the CPS. Not all tax units constructed this way from the CPS will necessarily be legally required to file and individual income tax return and therefore will not be represented on the SOI. Our algorithms determine which CPS tax units are likely to file an income tax return and these will comprise our Donor file (e.g. the “filers”) for matching with the PUF. The remaining CPS tax units are not required to file an income tax return, but they are represented in our final matched data set (e.g., the “non-filers”).

We perform the match by running seven (7) SAS programs in sequence. A brief description of these programs and their inputs and outputs follows.

1. CPS-PREP: This program prepares the CPS for processing. Person-level information is combined with family and household information to construct a composite record for each member of a CPS household. A statistical summary of the output files is produced.
    * Input files: ASEC2005_PUBUSE.PUB (March 2005 CPS File in ASCII format.)
    * Output files: HOUSHLD (SAS File of CPS household information) FAMPER (SAS File combining CPS Family and Person
level detail.)
2. CPS-RETS: Constructs CPS tax units from the composite files. Processes one household at a time; examines relationships among household members; and determines which members constitute a tax unit. Once a tax unit is constructed, we determine whether or not a tax return is required to be filed. We make this determination by examining the tax filing requirements contained in the IRS Instructions for tax year 2005.
   * Input files: HOUSHLD FAMPER
   * Output files: CPSRETS (SAS dataset representing the tax filers. The Donor file.) CPSNONF (SAS dataset representing the non-filers.)
3. SOI-RETS: Creates an extract from the 2004 PUF that will serve has the Host file in the statistical match.
   * Input files: PUF2004 (SAS Dataset containing the original PUF.)
   * Output files: SOIRETS (SAS Dataset containing the PUF Extract. The Host file.)
4. PHASE-1: Prepares both Host and Donor files for the match. Partitions each file along similar dimensions; constructs independent variables to be used in the predictive mean calculations; performs the predictive mean regressions within each partition; and merges the fitted values back to the original Host and Donor files. Our dependent variable in the regressions is taxable income (TINCX) on the PUF.
   * Input Files: SOIRETS CPSRETS
   * Output Files: BETA (SAS Dataset with regression coefficients.) CPSFILE (SAS Dataset extract for CPS.) SOIFILE (SAS Dataset extract for PUF.)
5. PHASE-2: Performs the match. Creates working extracts from SOIRETS and CPSRETS containing record identifiers and fitted values; sorts both files by the fitted values (YHAT) within each partition; scales the sample weights on the Donor file to ensure that weighted population counts are identical across Host and Donor files for each partition; and performs the match using the predictive mean matching algorithm.
   * Input files: SOIFILE CPSFILE
   * Output files: MATCH (SAS Dataset containing the results of the match: A record ID from the PUF, a record ID from the CPS and a newly-constructed, final match weight.
6. ADDCPSVARS: Creates a preliminary version of the Production file by linking the Donor records from the CPS with the matched file.
    * Input files: CPSRETS SOIRETS MATCH
    * Output files: PROD2004_V1 (SAS Dataset with preliminary version of the Production File.)
7. ADDNONFILERS: Adds non-filer records to the Production File. Maps CPS variables into their PUF counterpart to ensure a consistent record layout; gives each record a unique sequence number; and creates updated version of the Production File.
   * Input files: CPSNONF PROD2004_V1
   * Output files: PROD2004_V1 (Updates w/ non-filer records.)


# APPENDIX B – Brief Description of Predictive Mean Matching[^footnote11]

* <u>Partitioning</u>: Attempt to keep (unweighted) cell sizes to a minimum of 30 and a maximum of 500. Check the weighted cell counts for each of the partitions and check for unbalanced cells.
* <u>Estimation</u>: Fit a (weighted) linear model for two Y- and Z-variables as a function of the X-variables common to both files.
<table border="0">
 <tr>
    <td>Host File: A(X,Y)</td>
    <td>Donor File: B(X,Z)</td>
 </tr>
 <tr>
    <td>$Y_1 = F_1(X) = XB_1 + e_1$</td>
    <td>$Z_1 = F_1(X) = XB_1 + e_1$</td>
 </tr>
 <tr>
    <td>$Y_2 = F_2(X) = XB_2 + e_2$</td>
    <td>$Z_2 = F_2(X) = XB_2 + e_2$</td>
 </tr>
</table>
* <u>Predicted Values</u>: Calculate fitted values of all four variables on each file.
<table border="0">
 <tr>
    <td>Host File: A(X,Y)</td>
    <td>Donor File: B(X,Z)</td>
 </tr>
 <tr>
    <td>$Y_1^*,Y_2^*,Z_1^*,Z_2^*$</td>
    <td>$Y_1^*,Y_2^*,Z_1^*,Z_2^*$</td>
 </tr>
</table>
* <u>Align Partitions</u>: Scale the weights for each cell in the Donor File so that they are equal to the weights in the Host file. Next, sort cells on the predicted value of one of the Z-variables so records with the closest values of the match variables are ordered correctly.
* * <u>Perform Match</u>: Match each record in Host File to the closest Donor record, splitting records if necessary to ensure all the "weight" on the Donor records are used up.


[^footnote1]: In applied work, it is often the case that the two input data sources are from surveys taken over different time frames so that the weighted population totals are slightly different across the two files. In this case, it is a common procedure to "scale" one of the files (usually the Donor file) so that the weighted population totals agree.

[^footnote2]: Notice that this implies that the sum of the weights on File A must equal the sum of the weights on File B.

[^footnote3]: This is only the case when the weighted totals are the same on both files. Partitioning of the input files can further distort the marginal distribution of the Z’s.

[^footnote4]: The term was apparently first coined by Little (1986).

[^footnote5]: A partitioning scheme can also be implicitly "induced" by the careful construction of a distance metric. Imposing an arbitrarily large penalty for matches between certain types of records can have much the same effect as partitioning. In this sense, partitioning is equivalent to assigning an infinite distance to matches between certain records.

[^footnote6]: A PUF for tax year 2005 became available shortly after this project began, but because of differences in sample designs between the two years, we decided to rely on the 2004 PUF.

[^footnote7]: *The Urban-Brookings Tax Policy Center Microsimulation Model: Documentation and Methodology for Version 0304*, Rohaly et. al., January 10th, 2005.

[^footnote8]: As measured by the ratio between the CPS and PUF weighted record counts, several CPS cells in the TPC match were on the order of 2.0 to 2.5 times the PUF value.

[^footnote9]: *A Profile of Non-Filers*, Office of Tax Analysis Paper 78, U.S. Department of Treasury, Washington, DC.

[^footnote10]: The CPS is conducted in March of every calendar year and questions relating to the annual income of respondents refer to the <u>prior</u> year’s income. In contrast, the 2004 PUF reports income received during calendar year 2004.

[^footnote11]: This material is from “Statistical Matching Meeting”, March 24th, 2003, *Urban-Brookings Tax Policy Center*.