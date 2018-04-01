#!/bin/python
import os
import re
import json
from collections import namedtuple
import i3ipc
import getopt, sys
#from time import sleep
#from PyQt5 import QtCore
#from PyQt5.QtWidgets import QApplication, QWidget



class Workspace:
	
	def __init__(self,attr=None):
		self.data = None
		self.layout = None
		self.name = None
		self.path = ""

		if attr:
			self.setData(attr)
		else:
			self.data = {
			"num" 		: None,
			"name" 		: None,
			"visible" 	: None,
			"focused" 	: None,
			"rect" 		: None,
			"output" 	: None,
			"urgent" 	: None,
			"applications" : [],
			}

		self.layout = None
		self.get_layout()
		if self.data['name']:
			self.name = "workspace"+str(self.data['name'])

	def setData(self,attr):
		self.data = {
			"num" 		: attr[0],
			"name" 		: attr[1],
			"visible" 	: attr[2],
			"focused" 	: attr[3],
			"rect" 		: attr[4],
			"output" 	: attr[5],
			"urgent" 	: attr[6],
			"applications" : [],
			}

	def getWorkspaceName(self):
		return self.name

	def getData(self):
		return self.data

	def getVisible(self):
		return self.data['visible']	

	def getName(self):
		return self.data['name']	

	def getNum(self):
		return self.data['num']

	def getFocused(self):
		return self.data['focused']

	def getRect(self):
		return self.data['rect']

	def getOutput(self):
		return self.data['output']

	def getUrgent(self):
		return self.data['urgent']

	def getApps(self):
		return self.data['applications']

	def addApp(self,app):
		self.data['applications'].append(app)

	def getExec(self):
		return "i3-msg \""+self.name+"; append_layout "+self.path+"\"\n"

	def startApps(self):
		for elem in self.data['applications']:
			print(elem.get_cmd())

	def all(self):
		return self.workspace_information

	def active(self):
		return [ elem for elem in self.workspace_information if elem.visible]

	def focused(self):
		return [ elem for elem in self.workspace_information if elem.focused]

	def workspaces_information(self):
		cmd = os.popen("i3-msg -t get_workspaces")
		var = cmd.read()
		return json.loads(var,object_hook=lambda d: namedtuple("workspace", d.keys())(*d.values()))

	def get_related(self):
		apps = self.data['applications']
		for elem in apps:
			elem.get_related()

	def get_all_workspace_ids(self):
		cmd = "xwininfo -root -all -int | grep workspace"
		var = os.popen(cmd).read()
		var = var.split("\n")
		for elem in var:
			info = elem.split(":")
			if len(info) > 1:
				info[0] = info[0].split(" \"")
				info[0][0] = info[0][0].replace(" ","")
				if "workspace" in info[0][1]:
					info[0][1] = info[0][1].replace("[i3 con] ","")
				self.workspace_info[info[0][1]] = {"id" : info[0][0], "info" : info[1]}

	# get ĺayout form i3
	def get_layout(self):
		if not self.data:
			return
		cmd = "i3-save-tree --workspace " + str(self.data['num'] )
		self.layout = os.popen(cmd).read()

	#write the layout to json file
	def save_layout(self,path=""):
		self.path = path+self.name+".json"
		fd = open(self.path,'w')
		fd.write(self.layout)
		fd.close()

class Application():
	def __init__(self,Con):
		self.cmd = ""
		self.Con = Con
		self.pid = -1
		self.window = None
		self.get_window_information()

	def getExec(self):
		return "(exec "+ self.cmd +" & )\n"

	def get_window_information(self):		
		cmd = "xprop -id "
		grep = " | grep WM"
		
		if not self.Con.window:
			return

		window_cmd = cmd + str(self.Con.window) + grep
		data = os.popen(window_cmd).read()
		info = self.parse_window_information(data)

		if "_NET_WM_PID(CARDINAL)" in self.window:
			self.pid = self.window["_NET_WM_PID(CARDINAL)"]
			self.cmd = os.popen("cat /proc/"+self.pid+"/cmdline").read()

	def parse_window_information(self,data):
		data = data.split("\n")
		self.window = dict()
		for elem in data:
			if "=" in elem:
				elem = elem.split(" = ")
			elif ":" in elem:
				elem = elem.split(" : ")
			else:
				continue
			if len(elem)<2:
				continue
			self.window[elem[0]] = elem[1]

	def get_cmd(self):
		return self.cmd

	def get_name(self):
		return self.Con.name

	def rr(self,d):
		cmd = "pgrep -P "+d
		cm1 = "ps -ax | grep "+d
		cm1 = "cat /proc/"+d+"/cmdline"
		out = os.popen(cmd ).read()
		out = out.split("\n")
		tmp = os.popen(cm1 ).read()
		
		print("------------------------")
		print("Parent:",d,tmp)
		print("Childs:",out)
		print("------------------------")
		
		for elem in out:
			if elem:
				self.rr(elem)

	# how do i get all running applications???
	def get_related(self):
		
		self.rr(self.pid)
		print("##########################")


class WindowApplications():

	def __init__(self,path=''):
		self.workspaces =dict()
		self.window = dict()
		self.monitors = []
		self.i3 = i3ipc.Connection()
		self.tmp = None
		self.get_workspaces()
		self.get_workspace_applications()
		self.path = path

	def get_workspaces(self):
		cmd = os.popen("i3-msg -t get_workspaces")
		var = cmd.read()
		workspaces = json.loads(var,object_hook=lambda d: namedtuple("workspace", d.keys())(*d.values()))
		for elem in workspaces:
			self.workspaces["workspace "+str(elem[1])] = Workspace(elem)

	def get_workspace_applications(self):
		tree = self.i3.get_tree()
		leaves = tree.leaves()
		for elem in leaves:
			self.build_leave_tree(elem)

	def build_leave_tree(self,con):

		if not con:
			return

		if con.type != "workspace":
			self.build_leave_tree(con.parent)

		if con.type == "workspace":
			self.tmp = con.type +" "+con.name
			if self.tmp not in self.workspaces:
				self.workspaces[self.tmp] = Workspace()
			return
		self.workspaces[self.tmp].addApp(Application(con))

	def saveApplications(self,stype='sh',option='visible'):
		for key in self.workspaces:
			if 'visible' in option:
				if not self.workspaces[key].getVisible():
					continue
			if 'focused' in option:
				if self.workspaces[key].getFocused() == False:
					continue
			workspace = self.workspaces[key]
			apps = workspace.getApps()
			content = "#!/bin/sh\n\n"
			content += workspace.getExec()

			for elem in apps:
				content += elem.getExec()
			content +="\n"

			filename = self.path+workspace.getWorkspaceName()+".sh"
			fd = open(filename,"w")
			fd.write(content)
			fd.close()
			os.popen("chmod +x "+filename)

	def saveLayouts(self,option='visible'):
		for elem in self.workspaces:
			if 'visible' in option:
				if not self.workspaces[elem].getVisible():
					continue
			if 'focused' in option:
				if not self.workspaces[elem].getFocused():
					continue
			self.workspaces[elem].save_layout(path=self.path)

	def restore(self):
		for elem in self.window:
			print(elem,self.window[elem].startApps())

	def print_(self):
		for elem in self.workspaces:
			print(elem,":")
			self.workspaces[elem].startApps()

	def rel(self):
		for elem in self.workspaces:
			self.workspaces[elem].get_related()

	def getMonitors(self):
		cmd = "xrandr --listmonitors"
		var = os.popen(cmd).read()
		var = var.split("\n")
		self.monitors = []
		for elem in var:
			if elem:
				elem = elem.split(": ")
				try:
					index = int(elem[0])
				except Exception as e:
					continue			
				self.monitors.append(elem[1])
		return self.monitors


def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "ho:p:", ["help", "option=", "path="])
	except getopt.GetoptError as err:
		# print help information and exit:
		print(str(err))  # will print something like "option -a not recognized"
		sys.exit(2)
	path_ = '/home/simon/.config/layouts/'
	option_ = 'visible'
	for o, a in opts:
		if o == "-v":
			verbose = True
		elif o in ("-h", "--help"):
			
			sys.exit()
		elif o in ("-o", "--option"):
			option = a

		elif o in ("-p", "--path"):
			path = a
		else:
			assert False, "unhandled option"

	windows = WindowApplications(path=path_)
	windows.saveLayouts(option=option_)
	windows.saveApplications(option=option_)
if __name__ == "__main__":
    main()



#windows = WindowApplications()
#windows.saveLayouts(option='focused')
#windows.saveApplications(option='focused')
#windows.rel()

#app = QApplication(sys.argv)

#w = QWidget()
#w.resize(250, 150)
#w.move(500, 300)
#w.setWindowTitle('Simple')
#w.setWindowFlags(QtCore.Qt.Popup)
#w.show()

#sleep(5)

#w.hide()
    
#sys.exit(app.exec_())


