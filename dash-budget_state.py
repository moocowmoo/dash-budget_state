#!/usr/bin/env python

import subprocess
import sys
import time
import yaml

COLOR = True
GREEN = RED = WHITE = NORMAL = TEAL = ''
if COLOR:
    GREEN = '\x1b[32m'
    RED = '\x1b[31m'
    WHITE = '\x1b[1m'
    TEAL = b'\x1b[36m'
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
    future_block = current_block + (cycle_offset * cycle_length)
    budget = budget_days * .1 * min_blok_subsidy(future_block)
    next_cycle = cycle_length - (future_block % cycle_length)
    next_cycle_block = future_block + next_cycle
    next_cycle_distance = next_cycle_block - current_block
    print "next budget : {0:>5.2f} days - block {1:} ({2:>5} blocks)".format(
            ((next_cycle_distance * 2.5)/1440), next_cycle_block, next_cycle_distance )
    print "{0:<20} {1:>6} {2:>9} {3:>16}".format('name', 'yeas', 'payment', 'remaining')
    sys.stdout.write(TEAL)
    print "{0:<20}                {1:18.8f} ".format('estimated budget', budget)
    for pname in pay_order:
        p = proposals[pname]
        if p["RemainingPaymentCount"] < 1:
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

        budget -= p['MonthlyPayment']
        sys.stdout.write(budget > 0 and GREEN or RED)
        notfunded = budget > 0 and ' ' or 'insufficient budget'
        p["RemainingPaymentCount"] -= budget > 0 and 1 or 0
        print "{0:<20} {1:>6}  {2:8.2f} {3:16.8f} {4:}".format(pname, p['net_yeas'], p['MonthlyPayment'], budget, notfunded)
        if budget < 0:
            budget += p['MonthlyPayment']

if __name__ == "__main__":
    print "\ncurrent time      : %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z")
    print "current block     : %s\n" % current_block
    for r in range(0,3):
        print_budget(proposals, current_block, r)
        print NORMAL
