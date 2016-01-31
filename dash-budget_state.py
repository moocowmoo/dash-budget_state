#!/usr/bin/env python

import subprocess
import sys
import time
import yaml

COLOR = True
GREEN = RED = WHITE = NORMAL = ''
if COLOR:
    GREEN = '\x1b[32m'
    RED = '\x1b[31m'
    WHITE = '\x1b[1m'
    NORMAL = '\x1b[0m'

def run_command(cmd):
    return subprocess.check_output(cmd, shell=True).rstrip("\n")

def net_yeas(proposal):
    return proposal['Yeas'] - proposal['Nays']

proposals = yaml.load(run_command("dash-cli mnbudget show"))
for proposal in proposals:
    proposals[proposal]['net_yeas'] = net_yeas(proposals[proposal])

pay_order = sorted(proposals.keys(),
                   key=lambda n: proposals[n]['net_yeas'])[::-1]
current_block = int(run_command("dash-cli getblockcount"))
total_masternodes = int(run_command("dash-cli masternode count"))
cycle_length = 16616
budget_days = (576*30)

def min_blok_subsidy(nHeight):
    nSubsidy = float(5)  # assume minimum subsidy
    for i in range(210240, nHeight, 210240):
        nSubsidy -= nSubsidy/14
    return nSubsidy

def print_budget(proposals, current_block, cycle_offset):
    current_block = current_block + (cycle_offset * cycle_length)
    budget = budget_days * .1 * min_blok_subsidy(current_block)
    next_cycle = cycle_length - (current_block % cycle_length) + (cycle_offset * cycle_length)
    next_cycle_block = current_block + next_cycle
    print "next budget : {0:>5.2f} days - block {1:} ({2:>5} blocks)".format(
            ((next_cycle * 2.5)/1440), next_cycle_block, next_cycle)
    print "{0:<20} {1:>6} {2:>9} {3:>16}".format('name', 'yeas', 'payment', 'remaining')
    sys.stdout.write(WHITE)
    print "{0:<20}                {1:18.8f} ".format('estimated budget', budget)
    for pname in pay_order:
        p = proposals[pname]
        if ( p["RemainingPaymentCount"] - cycle_offset) < 1:
            # print " proposal %s payments fulfilled" % pname
            continue
        if p["BlockStart"] > next_cycle_block:
            # print " proposal %s pending" % pname
            continue
        if p["BlockEnd"] < next_cycle_block:
            # print " proposal %s expired" % pname
            continue
        if p["Yeas"] - p["Nays"] < int(total_masternodes/10):
            # print " proposal %s rejected" % pname
            continue
        budget = budget - p['MonthlyPayment']
        sys.stdout.write(budget > 0 and GREEN or RED)
        print "{0:<20} {1:>6}  {2:8.2f} {3:16.8f}".format(pname, p['net_yeas'], p['MonthlyPayment'], budget)

if __name__ == "__main__":
    print "\ncurrent time      : %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z")
    print "current block     : %s\n" % current_block
    for r in range(0,3):
        print_budget(proposals, current_block, r)
        print NORMAL
