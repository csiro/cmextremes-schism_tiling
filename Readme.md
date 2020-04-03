# SCHISM rechunking

## Introduction

Scripts written in snakemake to tile and chunk output from the SCHISM model.

In order to achieve fast time series access, it is required to concatenate the NetCDF files and apply chunking in the time dimension. For practical reasons involving file sizes, it becomes necessary to "tile" the data, or split it up spatially.

Because SCHISM is on an irregular grid indexed by node number, the divisions are not tiles in the traditional sense (lon/lat).

In the SCHISM output, variables can be a function of triangular grid element, and sometimes a function of node (vertex).

As it is tricky to cope with both of these in the chunking, it was decided to focus on the node variables. In the grid, there are 155083 nodes. We split these up (almost) equally into 103 groups (or "tiles").

The process of forming a tile is as follows.

1. For each year & month: extract the data for tile *n* using `ncks`

2. Concatenate over time all data for tile *n* using `ncrcat`

3. Apply chunking in time dimension using `nccopy`

For the baseline SCHISM scenario there are are (35 years) X (12 months) X (103 tiles) , so that is approximately 43000 extract tasks, plus 103 concatenations and 103 chunking jobs. As this could quickly become unmanageable ( and slow without parallelisation ), [Snakemake workflow tool](https://snakemake.readthedocs.io/) has been deployed for the task.

Snakemake allows the work to be specified in compact form. It will also compute all dependencies and apply the appropriate rule to do any work that needs to be done. It can easily be interrupted and resumed.

Jobs can be deployed in SLURM on the cluster and resources allocated to it can be adjusted (i.e. max number of simultaneous running jobs).

Snakemake has its own syntax although it is python-based, and python can be freely mixed with it. In addition, the rules may be carried out using python or bash shell.

## Quick run through the Snakefile

Looking at the Snakefiles, it is conceptually easier to work backwards starting from the desired file (tiled and chunked). These are specified under *rule all*.

Via the *output:* specification of *rule chunk*, this creates a need/dependency for concatenated tile files as inputs. The *shell:* directive specifies how to create chunked files from concatenated ones.

This brings us to *rule concat* which describes how to make concatenated files from individual monthly extracts. As inputs, it expects to see extracts for every tile, year and month.

This creates a dependency on *rule extract*. Here there expected SCHISM files are specified as inputs. The shell commands to perform the extracts is specified.

## Running on the cluster

In order to run on the cluster, it should be run on one of the pearcey interactive nodes as a supervisor. This could be run under a vnc session so as not to terminate on logout. Use this command

```bash
snakemake -s Snakefile.baseline  --printshellcmds --cluster 'sbatch -t {params.time} --mem={params.mem}' -j 50
```

This will trigger slurm jobs, maximum 50 at a time, that will perform the work.

The extract jobs are generally short, often 10 minutes or less, so this gets done fairly quickly, but it does take a few days to work through tens of thousands of tasks. If the cluster looks quiet, the 50 maximum could be increased, but you might run into disk bandwidth issues on the OSM.

## Quota issues

The snakemake job should be run on /scratch1 as a working directory due to space, bandwidth and file count quotas.

Snakemake will put many thousands of files into the *.snakemake* directory, more than your quota under /home.
It will also write thousands of slurm job output files. Sometimes you might have to stop the snakemake task (ctrl-C), delete these, then restart. The task remains to automatically clean up these files as the jobs progress.

