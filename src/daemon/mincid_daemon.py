#!/usr/bin/env python3
#
# A small http server that starts the CI process
#

import http.server
import syslog
from daemonize import Daemonize

from mincid.Project import Project

class MincidHttpServer(http.server.BaseHTTPRequestHandler):

    def __start_project(self, prj_name):
        syslog.syslog(syslog.LOG_INFO | syslog.LOG_USER,
                      "Starting project [%s]" % prj_name)
        try:
            project = Project(
                "/mincid/build/system/ci/system/mincid_master.json",
                "/mincid/build/system/ci/projects/%s.json" % prj_name)
            project.cleanup()
            project.process()
            syslog.syslog(syslog.LOG_INFO | syslog.LOG_USER,
                          "Project started [%s]" % prj_name)
        except FileNotFoundError:
            # Project does not exists
            self.send_error(404)
            syslog.syslog(syslog.LOG_INFO | syslog.LOG_USER,
                          "Project does not exists [%s]" % prj_name)
            return
        
        self.send_response(200, 'OK')
        self.send_header('Content-type', 'html')
        self.end_headers()
            
    def do_GET(self):

        if self.path.startswith("/mincid/start/"):
            self.__start_project(self.path[14:])

def main():
    server_address = ('', 8000)
    httpd = http.server.HTTPServer(server_address, MincidHttpServer)
    httpd.serve_forever()

def daemon():
    daemon = Daemonize(app="mincid_daemon", pid='/tmp/mincid.pid', action=main)
    daemon.start()
    
if __name__=='__main__':
    daemon()
