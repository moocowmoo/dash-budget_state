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

cycle_length = 16616
next_cycle = now_block % cycle_length
budget = 16616 * .1 * min_blok_subsidy(now_block)
def days(s):
    return 1

import time
print
print "current time      : %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z")

print "current block     : %s" % now_block
print "next budget cycle : %.2f days (%s blocks)" % (
        ((next_cycle * 2.5)/1440), next_cycle)
print
print "{0:<20} {1:<4} {2:<11} {3:>12}".format('name', 'approval', 'payment', 'remaining')
print "{0:<20}                {1:18.8f} ".format('estimated budget', budget)
for pname in pay_order:
    p = proposals[pname]
    if p["RemainingPaymentCount"] < 1:
        continue
    if p["BlockEnd"] < now_block:
        # print " proposal %s expired" % pname
        continue
    if p["Yeas"] - p["Nays"] < int(total_masternodes/10):
        # print " proposal %s rejected" % pname
        continue

    budget = budget - p['MonthlyPayment']
    print "{0:<20} {1:2.1f}%  {2:9.2f} {3:16.8f} ".format(pname, 100 * p['Ratio'], p['MonthlyPayment'], budget)

print
