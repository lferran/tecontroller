import argparse

from fibbingnode import CFG

import fibbingnode.misc.mininetlib as _lib
from fibbingnode.misc.mininetlib.cli import FibbingCLI
from fibbingnode.misc.mininetlib.ipnet import IPNet, TopologyDB
from fibbingnode.misc.mininetlib.iptopo import IPTopo

from fibbingnode.algorithms.southbound_interface import SouthboundManager
from fibbingnode.algorithms.ospf_simple import OSPFSimple

from mininet.util import custom
from mininet.link import TCIntf

from tecontroller.res.mycustomhost import MyCustomHost
from tecontroller.res.mycustomrouter import MyCustomRouter

from tecontroller.trafficgenerator.trafficgenerator import TrafficGenerator
from tecontroller.res import defaultconf as dconf

import networkx as nx

C1_cfg = '/tmp/c1.cfg'

C1 = 'c1' #fibbing controller
TG = dconf.TG_Hostname #traffic generator
LBC = dconf.LBC_Hostname #Load Balancing controller

R1 = 'r1'
R2 = 'r2'
R3 = 'r3'
R4 = 'r4'
D1 = 'd1'
S1 = 's1'
S2 = 's2'
D2 = 'd2'

BW = 1  # Absurdly low bandwidth for easy congestion (in Mb)



# Setting global data
SNMP_START_CMD = '/usr/sbin/snmpd -Lsd -Lf /dev/null -u snmp -I -smux -p /var/run/snmpd.pid -c /etc/snmp/snmpd.conf'

SNMP_WALK_CMD = 'snmpwalk -v 1 -c public -O e '

SNMP_WALK_OUT = 'dump.out'

COMMAND_BANNER = '\n\n*******************************************************************\n             MININET - SNMP WALK - DEMO APPLICATION                \n*******************************************************************\n\n'


class snmpTestTopo(IPTopo):
    def build(self, *args, **kwargs):
        """       +---+
               ___|R3 |__
            3 /   +---+  \3
             /            \
 +--+      +----+   10   +---+        +--+
 |S1|------| R1 |--------| R2|--------|D1|
 +--+      +----+        +---+_       +--+
              |            |   \_  
            +---+        +---+   +---+
            |C1 |        |LBC|   |TG |
            +---+        +---+   +---+
        """
        r1 = self.addRouter(R1, cls=MyCustomRouter)
        r2 = self.addRouter(R2, cls=MyCustomRouter)
        r3 = self.addRouter(R3, cls=MyCustomRouter)
        self.addLink(r1, r2, cost = 10)
        self.addLink(r1, r3, cost = 3)
        self.addLink(r3, r2, cost = 3)
        
        s1 = self.addHost(S1)
        d1 = self.addHost(D1)

        self.addLink(s1, r1)
        self.addLink(d1, r2)

        # Adding Fibbing Controller
        c1 = self.addController(C1, cfg_path=C1_cfg)
        self.addLink(c1, r1, cost = 1000)

class SimpleTopo(IPTopo):
    def build(self, *args, **kwargs):
        """       +---+
               ___|R3 |__
            3 /   +---+  \3
             /            \
 +--+      +----+   10   +---+        +--+
 |S1|------| R1 |--------| R2|--------|D1|
 +--+      +----+        +---+_       +--+
              |            |   \_  
            +---+        +---+   +---+
            |C1 |        |LBC|   |TG |
            +---+        +---+   +---+
        """
        r1 = self.addRouter(R1)
        r2 = self.addRouter(R2)
        r3 = self.addRouter(R3)
        self.addLink(r1, r2, cost = 10)
        self.addLink(r1, r3, cost = 3)
        self.addLink(r3, r2, cost = 3)
        
        
        s1 = self.addHost(S1)
        d1 = self.addHost(D1)

        self.addLink(s1, r1)
        self.addLink(d1, r2)

        # Adding Fibbing Controller
        c1 = self.addController(C1, cfg_path=C1_cfg)
        self.addLink(c1, r1, cost = 1000)


        # Adding Traffic Generator Host
        c2 = self.addHost(TG, isTrafficGenerator=True) 
        self.addLink(c2, r2)
        
        # Adding Traffic Engineering Controller
        c3 = self.addHost(LBC, isLBController=True)
        self.addLink(c3, r2)
 

class SIGTopo(IPTopo):
    def build(self, *args, **kwargs):
        """
                         +----+
                         | D1 |
                         +----+
                          |
            +---+        +---+      +---+
            | R2|--------|R3 |------|D2 |
            +---+       /+---+      +---+
              |     ___/   |
           10 |    /       |
              |   /        |
 +--+      +----+'       +---+        +--+
 |S1|------| R1 |--------| R4|--------|C1|
 +--+      +----+        +---+_       +--+
              |            |   \__
            +---+        +---+    \+---+
            |S2 |        |TG |     |LBC|
            +---+        +---+     +---+
        """
        r1 = self.addRouter(R1)
        r2 = self.addRouter(R2)
        r3 = self.addRouter(R3)
        r4 = self.addRouter(R4)
        self.addLink(r1, r2, cost=10)
        self.addLink(r1, r4)
        self.addLink(r2, r3)
        self.addLink(r3, r4)
        self.addLink(r1, r3)

        s1 = self.addHost(S1)
        d1 = self.addHost(D1)
        s2 = self.addHost(S2)
        d2 = self.addHost(D2)
        self.addLink(s1, r1)
        self.addLink(s2, r1)
        self.addLink(d1, r3)
        self.addLink(d2, r3)

        # Adding Fibbing Controller
        c1 = self.addController(C1, cfg_path=C1_cfg)
        self.addLink(c1, r4, cost=999)

        # Adding Traffic Generator Host
        #c2 = self.addHost(TG, isTrafficGenerator=True) 
        #self.addLink(c2, r4)

        # Adding Traffic Engineering Controller
        #c3 = self.addHost(LBC, isLBController=True)
        #self.addLink(c3, r4)


def launch_network():
    net = IPNet(topo=snmpTestTopo(),
                debug=_lib.DEBUG_FLAG,
                intf=custom(TCIntf, bw=BW),
                host=MyCustomHost)
    TopologyDB(net=net).save(dconf.DB_Path)
    net.start()
    FibbingCLI(net)
    net.stop()


    # Not used
def launch_controller():
    CFG.read(C1_cfg)
    db = TopologyDB(db=DB_path)
    manager = SouthboundManager(optimizer=OSPFSimple())
    import ipdb; ipdb.set_trace() #TRACEEEEEEEEEEEEEEE    
    manager.simple_path_requirement(db.subnet(R3, D1), [db.routerid(r)
                                                        for r in (R1, R2, R3)])
    manager.simple_path_requirement(db.subnet(R3, D2), [db.routerid(r)
                                                        for r in (R1, R4, R3)])
    try:
        manager.run()
    except KeyboardInterrupt:
        manager.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-c', '--controller',
                       help='Start the controller',
                       action='store_true',
                       default=False)
    group.add_argument('-n', '--net',
                       help='Start the Mininet topology',
                       action='store_true',
                       default=True)
    parser.add_argument('-d', '--debug',
                        help='Set log levels to debug',
                        action='store_true',
                        default=False)
    args = parser.parse_args()
    if args.debug:
        _lib.DEBUG_FLAG = True
        from mininet.log import lg
        from fibbingnode import log
        import logging
        log.setLevel(logging.DEBUG)
        lg.setLogLevel('debug')
    if args.controller:
        launch_controller()
    elif args.net:
        launch_network()
