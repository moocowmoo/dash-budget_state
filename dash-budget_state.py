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
    # {u'event_block_height': 664640, u'payment_amounts': u'195.79000000|120.00000000|13.00000000|95.00000000|5.00000000|321.90000000|2702.83000000|35.00000000|205.00000000|105.00000000|120.00000000|1731.36000000|25.00000000|20.00000000|20.00000000|119.00000000|215.00000000', u'type': 2, u'proposal_hashes': u'f5f90567f88f54e80b2c1e284879a9d7ac18daabfc5a7d70b25d20f793706429|ec520c66ac4c178ccceb005a274d6c606ecb5576362aa7a9cab4d59b2f6c44c0|e18b46cd7bbb89b4c25056c72f9907519b630c245c6ac7c04a2ea41f1d773c29|d4488afe7927a2d35390b5278758144a34c6abd24aade13103fd34f5259b0177|cb54a4b8b0500725a86b8c5b5680738c28377c10d9b8f3228b4c32a88ab3a16b|c553eba90e3cdac18a6a44f549e475032829417c811d749d37ed390be06a0518|aedd8e6a1b61c540f7f50bc83d472c2f438f601ffa6a0a8108aad368acb8e7e1|ab0f1d930f760659e817dae9d4cf249f6fca9aeff599f922fb9e8c1f30e01034|a1c11b117e441596bc271f5f7d77cddde045f99198f36ffda527f23dbd9f3dd2|98c231a945e425f2ec315301cb702d0df7e7e2549fff48e8cc75ca58bcc4fb03|7e69fd28e280e447c7c3a1efa7bbf6103d2b367f1b526033d4bcdc06374c2937|71a7984ae9777135f3685c1b060bd77460891fb0be17ee3dc94341f7b3ff2018|4a87cb70a026099deeec238ad99b8859799cd082f477308280c19d64c4588919|2f281256c88491666dc254514ba905010822cf10133c074d9497715ba2eb09f3|0f4ee0ecd5ed0a93df2eac697c592b6f9af8f2c008d64ec05d18f0d822c7e90f|0595cd74e9bb5a5411f3edf9f0c0658755cb2f76df89c4796f41b4faff5c0d50|039db789f67dc8cddaddc5a382d805615da9298cd6a14620aa4ef81fd5d96430', u'payment_addresses': u'XuBDpp4g6Tb7rXXwzprBJa2heWdHijmMky|XvzBvLjBbYQMEGknXw1SwjqVe4maXuMvRF|XjpwY2WiGiN8ia9FkxSDQMGC4TqbAEHZ3W|XsJTZUTCcenzz2xgMFpV8i5mpzzmNb1rnu|XhFbqM5cc16a6Qt6QjNQrCeU5dfnebeHTJ|XtwXUtJhyW52ZpzFu9grNMfAmcVDVkCj5G|XtspXMnoGt4RF23CZ7MQQ7NFmkAebMUNME|Xgaf1vyMxge3CnF47bD9eqdhffTqRkK1rE|Xy1wox12sP2JKqf9nBycMjArzsXgRL1nw9|XiGw3ohj59SJYGUboM2kpdwKHvER6JhrCK|Xyoq8CQa1MmJ1xafGQKMhCfsRFyxYaiJTY|XfNeikkfga1GUVt3TUE5XjB4jRhQXPPiKa|Xcq2b3xM5kM2prto8wVBFCXciTwG6s653J|Xkg5gmD8QbcnkduUqGR56VpNSNiNmReCN9|Xj3cH8ogS2seLxXcctgKdkzG2NXEf4mCVV|Xr8XcQug8GKWx24GcEMwYFFMBegym7NSSQ|XbXb6rUeDrPcCe9xyoGTBL7TDkBU46KTvv'}
    # finalized budget object -- TODO indicate voting is closed
    if int(p['_data']['type']) == 2:
        print p
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
