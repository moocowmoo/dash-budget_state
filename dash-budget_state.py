#!/usr/bin/env python

import subprocess
import sys
import time
import yaml
import json

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

def collate_votes(proposal):
    proposal['Yeas'] = 0
    proposal['Nays'] = 0
    proposal['Abstains'] = 0
    for hsh in proposal[u'votes']:
        b = proposal[u'votes'][hsh]
        (vindx,ts,val,mode) = [ b[16:80]+'-'+b[82:83] ] + list(b.split(':')[1:4])
        if val == 'YES':
            proposal['Yeas'] += 1
        elif val == 'NO':
            proposal['Nays'] += 1
        else:
            proposal['Abstains'] += 1


objects = yaml.load(run_command("dash-cli gobject list all"))
proposals = {}
for proposal in objects:
    p = objects[proposal]
    p['_type'], p['_data'] = json.loads(p[u'DataHex'].decode("hex"))[0]
    if str(p['_type']) == 'watchdog':
        continue
    if int(p['_data'][u'end_epoch']) < int(time.time()):
        continue
    proposals[proposal] = p['_data']
    proposals[proposal]['votes'] = json.loads(run_command('dash-cli gobject getvotes %s' % proposal))
    collate_votes(proposals[proposal])
    proposals[proposal]['net_yeas'] = net_yeas(proposals[proposal])

pay_order = sorted(proposals.keys(),
                   key=lambda n: proposals[n]['net_yeas'])[::-1]
current_block = int(run_command("dash-cli getblockcount"))
total_masternodes = int(run_command("dash-cli masternode count"))
cycle_length = 16616

def min_blok_subsidy(nHeight):
    nSubsidy = float(5)  # assume minimum subsidy
    for i in range(210240, nHeight, 210240):
        nSubsidy -= nSubsidy/14
    return nSubsidy

def print_budget(proposals, current_block, cycle_offset):
    future_block = current_block + (cycle_offset * cycle_length)
    next_cycle = cycle_length - (future_block % cycle_length)
    next_cycle_block = future_block + next_cycle
    next_cycle_distance = next_cycle_block - current_block
    cycle_epoch = time.strftime("%s",time.gmtime(time.time() + ((next_cycle_distance * 2.62)*60) ))
    budget = cycle_length * .1 * min_blok_subsidy(next_cycle_block)
    print "next budget : {0:>5.2f} days - block {1:} ({2:>5} blocks)".format(
            ((next_cycle_distance * 2.62)/1440), next_cycle_block, next_cycle_distance )
    print "{0:<30} {1:>6} {2:>9} {3:>16}".format('name', 'yeas', 'payment', 'remaining')
    sys.stdout.write(TEAL)
    print "{0:<30}                {1:18.8f} ".format('estimated budget', budget)
    for pname in pay_order:
        p = proposals[pname]
        if p["end_epoch"] < cycle_epoch:
            continue
        if p["net_yeas"] < int(total_masternodes/10):
            # print " proposal %s rejected" % pname
            continue

        budget -= float(p['payment_amount'])
        sys.stdout.write(budget > 0 and GREEN or RED)
        notfunded = budget > 0 and ' ' or 'insufficient budget'
#        p["RemainingPaymentCount"] -= budget > 0 and 1 or 0
        print "{0:<30} {1:>6}  {2:8.2f} {3:16.8f} {4:}".format(p['name'][:30], p['net_yeas'], float(p['payment_amount']), budget, notfunded)
        if budget < 0:
            budget += float(p['payment_amount'])

if __name__ == "__main__":
    print "\ncurrent time      : %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z")
    print "current block     : %s\n" % current_block
    for r in range(0,3):
        print_budget(proposals, current_block, r)
        print NORMAL
