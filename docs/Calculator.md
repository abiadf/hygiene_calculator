# Milking Cleaning Project


## Introduction
The Consumables team is working to sanitize the Astronaut milking robot tubing, using a solution composed of a chemical detergent mixed with water.

The team, is investigating the cleaning process. They collect data from their sensors, in csv files, which is to be analyzed. This data is present on here and in DataBricks, extracting the files from the cloud.

## Theory
The cleaning of an Astronaut deals with 3 main properties:
1. Temperature T, [C]
2. Conductivity C or $\sigma$, [mS/cm] or [%]
3. Flow F, [L/min]

Based on those, the cleaning, or rinsing, is composed of the following periods:
1. **Post-milking flush**: milk being flushed out of the Astronaut using water, to ignore. Consists of milk and water. Observable first peak in conductivity in graph
2. **Pre-rinse**: clean system of milk residue. Consists of water. Mostly interested in a large peak in flow.
3. **Hot Rinse**: consists of water and chemical. Temperature starts increasing a lot, conductivity increases then stabilizes, flow goes up and down. In this phase, the maximum temperature is achieved. Following this temperature maximum, temperature (and conductivity, but to ignore) starts dropping, but flow peaks. This marks the end of the hot rinse period.
4. **Post-rinse**: consists of cold water flushing the system to remove the chemical. Starts when hot rinse ends, so starts when there is a drop in temperature (and conductivity, but ignore), but a peak in flow. Note that sometimes the temperature and conductivity profiles are not dropping synchronously, so the post-rinse period is characterized by temperature dropping (not decreaseing).


## Goals
The goal of this project is to obtain the following:
- Maximum temperature value of entire dataset
- Get the average temperature of the time window (usually 2-min) which has the highest average temperature of the entire dataset
- Total time for which a criterion temperature (usually 72-77 C) is exceeded
- Measured average conductivity during the `hot rinse' period, in both [mS/cm] and [%]


## How to get the conductivity?
Use this diagram for visualization.
![](./docs/diagram_of_phases.png)


The following is done to get the electrical conductivity of the chemical cleaning agent:
0. Find milk flush peak: first peak in conductivity is due to the milk being flushed away with air, should be ignored
1. Get conductivity of water $\sigma_w$: since the chemical is always mixed with water. This should be done when only water is in the system, so in the cold pre-rinse; this is the best time to take the conductivity of water, which is when conductivity is at its minimum, but not 0 (usually around 0.3 mS/cm), take the average of that for a given duration (sometimes 100s, but if period is not low, take 20s at least)
2. Get conductivity of chemical and water solution $\sigma_(w+c)$: this is during the hot rinse. Need to take average of conductivity of the whole hot rinse $\sigma_(w+c)$
3. Get conductivity of chemical σ_c: subtract conductivity of water, so $\sigma_c = \sigma_(w+c) - \sigma_w$

### Notes
In acid cleaning, the conductivity is lower (~3 mS/cm in acid, while for alkaline ~10 mS/cm). Acid plots are trickier


## Data Processing

### Algorithm
This code aims to replace the manual data processing. First, it fetches the files, then extracts their info, then applies some processing like smoothening and filling, then does calculations to figure out the different phases.
