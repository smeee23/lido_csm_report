# The State of the Nodes

## Project Description

_The State of the Nodes_ is a tool designed to analyze data from [rated.network](https://rated.network), a well-known API that provides detailed insights into Ethereum's staking ecosystem. This project focuses on Lido's Community Staking Module (CSM) and its node operators. 

The project processes data to create visualizations and comparisons, offering insights into:
- The performance of individual node operators in the CSM.
- The overall performance of the CSM module.
- How the CSM module compares to all Lido node operators.

By providing these insights, the project aims to help users better understand operator performance and contribute to transparency in the staking ecosystem.

---

## Features

- **Data Processing**: Fetches and processes data from rated.network.
- **Time Series Visualizations**: Generates time series charts comparing an operator's performance to the CSM module as a whole and the Lido ecosystem, enabling operators to track their performance over time.
- **Ranking Insights**: Creates histograms using individual CSM operator data, allowing operators to see where they rank among their peers.
- **Customizable Data Analysis**: Processes data for specific days or computes multi-day moving averages (MVA) to provide a broader performance trend.
- **Comparative Insights**: Highlights differences between individual operators, the CSM module, and the larger Lido ecosystem.

---

## Variables and Their Descriptions

Below is a list of variables from the JSON data used in the project. 

| Variable                 | Description                           |
|--------------------------|---------------------------------------|
| `startEpoch`             | The starting epoch of data. An epoch is the time taken for 30,000 blocks to be completed on the chain. Each epoch has 32 slots. |
| `endEpoch`               | The ending epoch of data. |
| `startTimestamp`         | The starting date/time of data. |
| `endTimestamp`           | The ending date/time of data. |
| `startSlot`              | The starting slot of data. Slots are twelve-second periods of time where blocks can be added to the chain. They can be empty, if no block is created during that slot. |
| `endSlot`                | The ending slot of data |
| `validatorCount`         | The number of validator pubkeys that map to said entity. |
| `totalUniqueAttestations`| The total number of unique attestations. |
| `sumMissedAttestations`  | The total number of missed attestations. |
| `sumMissedSyncSignatures`| The total number of missed sync signature. (None if no sync committee) |
| `sumCorrectHead`         | The number of correct head votes found in said index’s attestations. |
| `sumCorrectTarget`       | The number of correct target votes found in said index’s attestations. |
| `sumCorrectSource`       | The number of correct source votes found in said index’s attestations. |
| `sumWrongHeadVotes`      | The number of incorrect head votes found in said index’s attestations. |
| `sumWrongTargetVotes`    | The number of incorrect target votes found in said index’s attestations. |
| `sumLateTargetVotes`     | The number of late target votes found in said index’s attestations. |
| `sumLateSourceVotes`     | The number of late source votes found in said index’s attestations. |
| `avgAttesterEffectiveness`| The aggregate attester effectiveness over the requested time period, that applies to said entity. |
| `sumInclusionDelay`      | The total inclusion delay for a period. Useful when computing the average inclusion delay of arbitrary periods. |
| `sumSyncSignatureCount`  | The total number of sync signatures. (None if no sync committee) |
| `avgInclusionDelay`      | The average inclusion delay over the requested time period, that applies to said entity. |
| `avgUptime`              | The average uptime (or participation rate) over the requested time period, that applies to said index. |
| `avgCorrectness`         | The aggregate attestation correctness accross all active validators in the network. |
| `avgProposerEffectiveness`| The aggregate proposer effectiveness over the requested time period, that applies to said entity. (None if no proposal) |
| `avgValidatorEffectiveness`| The aggregate validator effectiveness over the requested time period, that applies to said index. |

---

## Getting Started
