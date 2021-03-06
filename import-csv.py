#!/usr/bin/python
import csv
import os
import yaml

from graphviz import Digraph
import hashlib

dot = Digraph('Signals',format='svg')
dot.graph_attr['rankdir'] = 'LR'
dot.graph_attr['title'] = 'ECU Signals'
dot.node_attr['shape'] = 'box'
dot.node_attr['style'] = 'filled'
dot.edge_attr['fontsize'] = '10'

by_signal = {}
by_ecu = {}
input_dir = './input'
log_md=open("output.md", 'wb')

__SHORT_NAME__ = 'Signal Name (Short Name)'
__LONG_NAME__  = 'Signal Name (Long Name)'
__SUBSCRIBER__ = 'Subscriber'
__PUBLISHER__  = 'Publisher'
__SENDING__    = 'Sending'
__RECEIVERING__  = 'Receiving'

def hash_color(data):
    color = hashlib.md5(data)
    return '#' + hashlib.md5(data).hexdigest()[:5]

all_ecus = set()

for subsystem in os.listdir(input_dir):
    if(not subsystem.endswith('.csv')):
        print 'Looks like not csv file: {}, ignore'.format(subsystem)
        continue
    print 'Loading CSV file {}'.format(subsystem)
    log_md.write("{}\n==========================\n".format(subsystem))
    with open("{}/{}".format(input_dir,subsystem), 'rb') as csvfile:
        subsystem = subsystem[:-4]
        reader = csv.DictReader(csvfile,skipinitialspace=True)
        #print reader.fieldnames
        log_md.write("|{}|\n| ".format("|".join(reader.fieldnames)))
        for i in range(len(reader.fieldnames)):
            log_md.write("--- |")
        for row in reader:
            log_md.write("\n|")
            for i in range(len(reader.fieldnames)):
                cell = row[reader.fieldnames[i]]
                if (cell):
                    cell = '\\|'.join([ '`{}`'.format(i) for i in cell.split('|') ])
                log_md.write(cell)
                log_md.write(" |")

            signal_long_name  = row[__LONG_NAME__]
            signal_short_name = row[__SHORT_NAME__]
            publisher   = row[__PUBLISHER__]
            subscribers = row[__SUBSCRIBER__].split('|')
            if(publisher not in all_ecus):
                all_ecus.add(publisher)
                dot.node(publisher,publisher, color=hash_color(publisher))


            by_ecu.setdefault(publisher, {})
            by_ecu[publisher].setdefault(__SENDING__, {})
            by_ecu[publisher][__SENDING__].setdefault(signal_long_name, {})
            by_ecu[publisher][__SENDING__][signal_long_name].setdefault(subsystem, [])
            by_ecu[publisher][__SENDING__][signal_long_name][subsystem] += subscribers
            by_ecu[publisher][__SENDING__][signal_long_name][subsystem] = list(set(by_ecu[publisher][__SENDING__][signal_long_name][subsystem]))

            for subscriber in subscribers:
                if(subscriber not in all_ecus):
                    all_ecus.add(subscriber)
                    dot.node(subscriber,subscriber, color=hash_color(subscriber))
                dot.edge(publisher,subscriber,label="{}::{}".format(subsystem,signal_short_name), tooltip=signal_long_name, color=hash_color(signal_long_name), fontcolor=hash_color(signal_long_name))
                by_ecu.setdefault(subscriber, {})
                by_ecu[subscriber].setdefault(__RECEIVERING__, {})
                by_ecu[subscriber][__RECEIVERING__].setdefault(signal_long_name, {})
                by_ecu[subscriber][__RECEIVERING__][signal_long_name].setdefault(subsystem,[])
                by_ecu[subscriber][__RECEIVERING__][signal_long_name][subsystem].append(publisher) #no dedup here, expecting array length to be 1

            by_signal.setdefault(signal_long_name, {})
            by_signal[signal_long_name].setdefault(subsystem, {})
            by_signal[signal_long_name][subsystem].setdefault(__SUBSCRIBER__, [])
            by_signal[signal_long_name][subsystem][__SHORT_NAME__] = signal_short_name
            by_signal[signal_long_name][subsystem][__PUBLISHER__] = publisher
            by_signal[signal_long_name][subsystem][__SUBSCRIBER__] += subscribers
            by_signal[signal_long_name][subsystem][__SUBSCRIBER__] = list(set(by_signal[signal_long_name][subsystem]['Subscriber']))
    log_md.write("\n\n")
print '========================='
log_md.write('\nGenerated Data\n==========================\n\n```yaml\n')
log_md.write('{}```'.format( yaml.dump(by_ecu,default_flow_style=False)))

log_md.write('\nGenerated Graphviz Source\n==========================\n\n```dot\n')
log_md.write(dot.source)
log_md.write('\n```\n\n![graphviz](https://williamjoy.github.io/signal-matrix/graph.dot.svg)')
print 'Writing graphviz file graph.dot'
dot.render('graph.dot')
print 'Writing svg file graph.dot.svg'

with open('output/database.yaml', 'w') as output_file:
    print 'Writing to output/database.yaml'
    yaml.dump(by_ecu, output_file, default_flow_style=False)
with open('output/by_signal.yaml', 'w') as output_file:
    yaml.dump(by_signal, output_file, default_flow_style=False)
