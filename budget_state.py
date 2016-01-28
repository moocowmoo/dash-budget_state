#!/usr/bin/env python

import subprocess
import yaml

def run_command(cmd):
    return subprocess.check_output(cmd, shell=True).rstrip("\n")

def min_blok_subsidy(nHeight):
    nSubsidy = float(5)  # assume minimum subsidy
    for i in range(210240, nHeight, 210240):
        nSubsidy -= nSubsidy/14
    return nSubsidy

proposals = yaml.load(run_command("dash-cli mnbudget show"))
pay_order = sorted(proposals.keys(),
                   key=lambda n: proposals[n]['Ratio'])[::-1]
now_block = int(run_command("dash-cli getblockcount"))
total_masternodes = int(run_command("dash-cli masternode count"))

budget = 16616 * .1 * min_blok_subsidy(now_block)

print
print "estimated minimum budget: %s" % budget

print "{0:>16} {1:<5} {2:<22} {3:<11}".format('remaining', 'approval', 'name', 'payment')
for pname in pay_order:
    p = proposals[pname]
    if p["BlockEnd"] < now_block:
        # print " proposal %s expired" % pname
        continue
    if p["Yeas"] - p["Nays"] < int(total_masternodes/10):
        # print " proposal %s rejected" % pname
        continue

    budget = budget - p['MonthlyPayment']
    print "{0:16.8f} {1:2.1f}%    {2:<20} {3:9.2f}".format(budget, 100 * p['Ratio'], pname, p['MonthlyPayment'])

print
