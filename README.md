# LTA — Logging Trail Analyzer

Logging Trail Analyzer (LTA) is a Python-based workflow for deriving and evaluating logging trail networks from forest-machine GNSS data.

## Overview

LTA processes GNSS tracks recorded by harvesters and forwarders and converts them into a consolidated representation of the logging trail network.

The workflow is designed to:

1. derive logging trail centrelines from GNSS tracks;
2. estimate the number of machine passes along trail segments;
3. calculate spatial and operational characteristics of the logging trail network; and
4. produce maps for visualizing the resulting trail network and machine traffic.

The analysis includes measures of trail length and density, machine travel distance, trail area, trail spacing, forest accessibility, and spatial configuration of the logging trail network.

## Related research

The methodology is associated with the research article:

**Uusitalo, J., Mao, Z., Cao, S. & Abdi, O. (2026).  
Assessing logging trail network performance using spatial configuration metrics.  
Silva Fennica 60(3), article 26018.**

https://doi.org/10.14214/sf.26018

The study introduces spatial configuration metrics for evaluating logging trail networks beyond conventional measures such as trail density and mean trail spacing.
