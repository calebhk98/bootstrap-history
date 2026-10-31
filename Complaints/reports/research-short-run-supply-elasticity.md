# Research: short-run supply elasticity of staple and craft output to own price

Input to Complaint 960 (the working share of a producer at break-even is the steepest point of its curve). Labels:
**[read]** (full text or abstract page opened in this session), **[snippet]** (search-result text only, not opened),
**[no source found]**.

## Sources
- **Schneider 2012** [read, full text]. Eric B. Schneider, "Prices and Production: Agricultural Supply Response in
  Fourteenth-Century England", Oxford Discussion Papers in Economic and Social History 97
  (nuff.ox.ac.uk/Economics/History/Paper97/schneider97.pdf). Nerlove partial-adjustment model on acreage sown, bishop
  of Winchester manors, 1349-70.
  - Aggregate short-run elasticity of acreage to lagged own price (Table 1, wheat): not significant, coefficients
    near zero or slightly negative; barley (Table 2): 0.028 (not significant), 0.045 against oats (10 per cent),
    0.035 against the wage (5 per cent); oats (Table 3): not significant or negative. Long-run values are only
    slightly larger (about 0.04 to 0.07 for barley).
  - Table 5 of the same paper lists short-run wheat elasticities from other studies: 0.09 Hungary and 0.42 Germany
    (late 19th century, Eddie 1971), 0.0278 Missouri and 0.3053 Wisconsin (Fisher and Temin 1970), 0 to 0.08 Punjab
    (Krishna 1963); barley 0.19 Hungary, 0.27 Germany, 0.39 Punjab. These are second-hand (I did not open Eddie,
    Fisher and Temin, or Krishna); the paper says Higgs questioned Fisher and Temin's price variable. Latin America
    values in the text (0.21 to 0.83 Argentina, 0.37 to 1.30 Chile, from the paper's footnotes) are likewise
    second-hand.
  - The dependent variable is area sown, not output; the paper notes that yield response to input costs is left out.
- **Haile, Kalkuhl and von Braun 2016** [read, abstract page only]. "Worldwide Acreage and Yield Response to
  International Price Change and Volatility: A Dynamic Panel Data Analysis for Wheat, Rice, Corn, and Soybeans",
  Amer. J. Agric. Econ. 98(1): 172-190 (ideas.repec.org/a/oup/ajagec/v98y2016i1p172-190..html). Abstract: "own-price
  supply elasticities range from about 0.05 to 0.40" depending on the crop. Per-crop values and the horizon were not
  read (full text not opened). Search snippets attributed 0.05 to 0.15 short-run acreage elasticities to an earlier
  working paper by the same authors [snippet only].
- **Vertier, Jacolin, Mien and Leon 2025** [read, abstract page only]. "Critical Minerals: Estimating Price Elasticity
  of Supply Using Mine-Level Data", Banque de France Working Paper 1002 (ideas.repec.org/p/bfr/banfra/1002.html).
  Abstract: a significantly positive price elasticity of supply "reaching 50% on average", five years after a demand
  shock, eight minerals, 2000-2019, driven by silver, copper and nickel. This is a modern mine-level result over five
  years, not a one-year or pre-industrial figure. (A search summary gave different dates and horizon; the abstract
  page was taken.)
- **Askari and Cummings 1977** (survey), **Nerlove and Bessler 2001** (survey) [snippet only]: named as the standard
  surveys of supply-response estimates; not opened. Nerlove 1958 [not opened].
- Snippets that say short-run acreage responses are low and long-run larger (South African sunflower 0.238, Japanese
  rice acreage 1883-1969) [snippet only; the Japanese rice PDF was a scan I could not read].

## No source found
- A short-run supply elasticity for pre-industrial craft or workshop output: no source found.
- A pre-industrial mining output elasticity: no source found (the 2025 paper above is modern).
- Any estimate that separates the extensive margin of a fixed plant (the share of workplaces that run) from the
  intensive one (area, yield, inputs); every number above is a total response of area sown.

## What applies here
- Crop acreage elasticities in one year run from about zero (medieval England, Punjab wheat) to about 0.4 (Germany,
  Haile et al. upper end). The producer's run share in `producers.share_working` is the nearest counterpart to acreage:
  capacity already built, a choice of how much to use.
- The model's local elasticity at break-even was about 2.3 to 2.7 with the old declared spread; every opened source is
  five to fifty times lower. The old figure had no source.
- No source separates crops from crafts or mines in the one-year horizon, so one figure covers all recipes. The
  data has no field that distinguishes them in a way the sources support.
- The figure used (0.225) is the midpoint of the Haile et al. range, a judgement, not a measurement; confidence D.
  The Schneider medieval results sit at the bottom of that range, so a medieval start arguably wants lower still.
- Limits of the derivation: a log-normal spread with one elasticity fixes how steeply the share falls far below
  break-even too. At the derived spread a producer whose revenue is a tenth of its cost still runs about a quarter of
  its capacity (measure with `producers.share_working(0.1, 1.0)`), which no source supports; a closure rule or a
  non-normal cost distribution would be needed to keep the near-margin elasticity low without that tail.
