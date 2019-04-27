import base64
import ssl
import urllib.request
import json
from nsxwatch import models, db


class Nsx:
    def __init__(self):
        self.demo = models.Setting.query.filter_by(setting_name='demo').first().setting_value
        self.nsx_ip = models.Setting.query.filter_by(setting_name='nsx_host').first().setting_value
        self.username = models.Setting.query.filter_by(setting_name='nsx_user').first().setting_value
        self.password = models.Setting.query.filter_by(setting_name='nsx_pass').first().setting_value

    def nsxSetup(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.verify_mode = ssl.CERT_NONE
        httpsHandler = urllib.request.HTTPSHandler(context=context)

        manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        authHandler = urllib.request.HTTPBasicAuthHandler(manager)

        opener = urllib.request.build_opener(httpsHandler, authHandler)
        urllib.request.install_opener(opener)

        basicAuthString = '%s:%s' % (self.username, self.password)
        field = base64.b64encode(basicAuthString.encode('ascii'))
        self.authorizationField = 'Basic %s' % str(field, 'utf-8')

    def nsxReturnJson(self, url):
        request = urllib.request.Request(url,
                                         headers={'Authorization': self.authorizationField,
                                                  'Accept': 'application/json'})
        response = urllib.request.urlopen(request)

        json_dict = json.loads(response.read().decode())
        return json_dict

    def getJsonApiData(self, api_url, demo_file):
        if self.demo:
            with open(demo_file) as f:
                api_data = json.load(f)
        else:
            full_url = 'https://' + self.nsx_ip + api_url
            api_data = self.nsxReturnJson(full_url)

        return api_data

    def getNSXInfo(self):
        api_data = self.getJsonApiData('/api/1.0/appliance-management/global/info',
                                       'nsxwatch/demo/demo-info.json')
        return api_data

    def getJsonPoolStats(self, nsx_edge_id):
        api_data = self.getJsonApiData('/api/4.0/edges/' + nsx_edge_id + '/loadbalancer/statistics',
                                  'nsxwatch/demo/demo-lb.json')
        return api_data

    def getJsonPoolConfigs(self, nsx_edge_id):
        api_data = self.getJsonApiData('/api/4.0/edges/' + nsx_edge_id + '/loadbalancer/config/pools',
                                  'nsxwatch/demo/demo-lb-pools-config.json')
        return api_data

    def getJsonEdges(self):
        api_data = self.getJsonApiData('/api/4.0/edges',
                                       'nsxwatch/demo/demo-edges.json')
        return api_data

    def createEdges(self):
        edges = []
        edge_config = self.getJsonEdges()

        for edge in edge_config['edgePage']['data']:
            if edge['edgeType'] == 'gatewayServices':
                x = models.Edge(edge['objectId'],
                                edge['name'],
                                edge['edgeStatus'])
                try:
                    db.session.add(x)
                    db.session.commit()
                except:
                    db.session.rollback()
                edges.append(x)
        return edges

    def createPools(self):
        pools = []

        for edge_obj in models.Edge.query.all():
            lb_config = self.getJsonPoolConfigs(edge_obj.edgeid)
            lb_stats = self.getJsonPoolStats(edge_obj.edgeid)

            for pool in lb_config['pool']:
                x = models.Pool(edge_obj.id,
                                pool['poolId'],
                                pool['name'],
                                pool['algorithm'])
                try:
                    db.session.add(x)
                    db.session.commit()
                except:
                    db.session.rollback()
                pools.append(x)

            for pool in lb_stats['pool']:
                for pool_obj in models.Pool.query.all():
                    if pool_obj.poolid == pool['poolId']:
                        pool_obj.total_sessions = pool['totalSessions']
                        pool_obj.status = pool['status']
                        pool_obj.current_sessions = pool['curSessions']
                        pool_obj.bytesin = pool['bytesIn']
                        pool_obj.bytesout = pool['bytesOut']
                        db.session.commit()
        return pools

    def createPoolMembers(self):
        members = []

        for edge_obj in models.Edge.query.all():
            lb_config = self.getJsonPoolConfigs(edge_obj.edgeid)
            lb_stats = self.getJsonPoolStats(edge_obj.edgeid)

            for pool in lb_config['pool']:
                for member in pool['member']:
                    if member['condition'] == "enabled":
                        enabled = True
                    else:
                        enabled = False
                    poolid = models.get_poolkey_from_poolid(pool['poolId'])
                    x = models.Member(poolid,
                                      member['memberId'],
                                      member['name'],
                                      enabled)
                    try:
                        db.session.add(x)
                        db.session.commit()
                    except Exception as e:
                        print(e)
                        # Need to update all fields (except ID) instead of rollback
                        db.session.rollback()
                    members.append(x)

            for pool in lb_stats['pool']:
                for member in pool['member']:
                    for member_obj in models.Member.query.all():
                        if member_obj.memberid == member['memberId']:
                            member_obj.status = member['status']
                            member_obj.bytesin = member['bytesIn']
                            member_obj.bytesout = member['bytesOut']
                            member_obj.sessions_handled = member['totalSessions']
                            member_obj.failure_cause = ""
                            try:
                                member_obj.last_state_change_time = member['lastStateChangeTime']
                            except:
                                member_obj.last_state_change_time = 'Never'
                            db.session.commit()

        return members


def epoch_to_human(epoch):
    import time

    return time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(epoch))


nsx = Nsx()
nsx.nsxSetup()

if models.db_check()[0]:
    print(models.db_check()[1])
else:
    edges = nsx.createEdges()
    pools = nsx.createPools()
    members = nsx.createPoolMembers()

    for edge in edges:
        print(edge.name)
        print(edge.status)

    for pool in pools:
        print(pool.name)
        print(pool.algorithm)

    for member in members:
        print(member.name)
        print(member.enabled)
        print(member.status)
        print(member.bytesin)
