#!/usr/bin/python3

#################################################################################
## Monitor de Estado de Equipos y Servicios para AibeCloud
## Creado por Zasylogic S.A.
## Fecha : 2018
version = "0.3.9"
#monitortype = "CLOUD"
## Email: info@zasylogic.com
## Este Script chequea el uso de CPU, memoria, discos y estado de servicios
## Para lanzar manualmente: PowerShell_ISE
##################################################################################

import json
#import urllib.request
#import http.client, urllib.parse
from requests import post
import socket
import subprocess
#import shlex
import psutil
import os
from platform import system
import time
from xml.dom import minidom
import xml.etree.ElementTree as et
import smtplib
from email.mime.text import MIMEText
#from time import sleep
from glob import glob


#import platform

#jsonFile = open("../config.json", "r")
#jsonData = jsonFile.read()
#print(jsonData)
#data_string = json.loads(jsonData)
#print (data_string["vars"])
#print (data_string["vars"]["disablealerts"]["minini"])

if (psutil.WINDOWS):

	try:
		jsonFile = open('C:\\AibeCloudSystem\\scripts\\Saas\\Monitor\\config.json', "r")
		jsonData = json.loads(jsonFile.read())
		jsonFile.close()
	except:
		jsonFile = open('C:\\AibeSystem\\Saascripts\\config.json', "r")
		jsonData = json.loads(jsonFile.read())
		jsonFile.close()
else:
		jsonFile = open("/ZASYScripts/SyncAibe/monitorpbx/config.json", "r")
		jsonData = json.loads(jsonFile.read())
		jsonFile.close()

monitortype= jsonData["vars"]["typeserver"]
maxMem = jsonData["vars"]["maxmem"]
maxCpu = jsonData["vars"]["maxcpu"]
maxDrive = jsonData["vars"]["maxdrive"]
maxCount = jsonData["vars"]["maxcount"]
refreshTime = jsonData["vars"]["refreshtime"]
SentOk = jsonData["vars"]["sentok"]
outfile = jsonData["vars"]["outfileC"]
ddbbLimit = 1.1
pbxname = jsonData["vars"]["pbxname"]
pbxurl = jsonData["vars"]["pbxurl"]
maxping = jsonData["vars"]["maxping"]
maxPendRec = jsonData["vars"]["maxpendrec"]
maxPendRec = jsonData["vars"]["maxpendrec"]
getUrl = jsonData["vars"]["geturl"]
# Variables para envio de correo
smtpServer = jsonData["vars"]["smtpserver"]
smtpUser = jsonData["vars"]["smtpuser"]
smtpPass = jsonData["vars"]["smtppass"]
smtpFrom = jsonData["vars"]["smtpfrom"]
smtpTo = jsonData["vars"]["smtpto"]

# Variables de apoyo
if (jsonData["vars"]["computername"] == "" ): computername = (socket.gethostname()).upper()
else: computername = (jsonData["vars"]["computername"]).upper()

if (jsonData["vars"]["messagesubject"] == ""): messageSubject = "Monitor de estado de " + computername
else: messageSubject = jsonData["vars"]["messagesubject"]


################### sendmail ###################

def sendmail(smtpServer, smtpFrom, smtpTo, messageSubject, messageBody):
	#print(smtpUser)
	#print(smtpPass)

	msg = MIMEText(messageBody,'html', _charset="utf-8")
	msg["From"] = smtpFrom
	msg["To"] = smtpTo
	msg["Subject"] = messageSubject


	# Datos
	username = smtpUser
	password = smtpPass

	try: # Enviando el correo
		server = smtplib.SMTP(smtpServer)
		server.starttls()
		server.login(username,password)
		server.sendmail(smtpFrom, smtpTo, msg.as_string())
		server.quit()
		#print("Email enviado correctamente")
	except (socket.gaierror, socket.error, socket.herror, smtplib.SMTPException):
		log = open ('monitor.log','a')
		log.write(f'---------------------------------------------------------------------------------------------------\n')
		log.write(f'{time.strftime("%b %d %y")} {time.strftime("%X")} -- Error al enviar email\n')
		log.close()

################### end sendmail ###################

AibeStatus=[]
AibeCount=[]
for i in range(50): AibeStatus.append(0), AibeCount.append(0)

if (psutil.WINDOWS):
	j=0
	while(j < 1):
		j +=1
		if monitortype == "CLOUD":
			ddbbFile = open("C:\\AibeCloudSystem\\scripts\\Saas\\Monitor\\ddbb_space.json", "r")
			ddbb_space = json.loads(ddbbFile.read())
			ddbbFile.close()
			ddbbbrute = ddbb_space["vars"]["ddbb_space"] / 1000000
			rarbrute = ddbb_space["vars"]["rar_space"] / 1000000
			ddbbint = round(ddbbbrute)
			rarint = round(rarbrute)


		#print(subprocess.getoutput("top -d 1 -b -n2 | grep 'Cpu(s)' | tail -n 1"))

		i=0

		#Avarege CPU
		AVGProc = psutil.cpu_percent(interval=1)

		#Memoria
		OS = psutil.virtual_memory().percent

		volc = round(psutil.disk_usage('c:').percent)
		try:
			vold = round(psutil.disk_usage('d:').percent)
		except:
			vold = 0

		try:
			vole = round(psutil.disk_usage('e:').percent)
			eFreeSpace = psutil.disk_usage('e:').free/1000000
		except:
			vole = 0
			eFreeSpace = 0

		aibeTest = os.path.isfile("C:\\AibeCloudSystem\\AibeCloud\\App_Data\\ErrorOnStart.log")

		if (monitortype != "CLOUD" ):
			#adsservices = Get-WmiObject -query "Select * from Win32_Service Where Name like '%advantage%'"
			#aibeservices = Get-WmiObject -query "Select * from Win32_Service Where Name like '%aibe%'"
			ddbbHealth = "OK"
		else:
			if ((eFreeSpace - (ddbbint*ddbbLimit) - (rarint * 7)) < 0):
				ddbbHealth = f"KO - Necesarios {ddbbint}Mb + {rarint}Mb(*7) . Restante {eFreeSpace}) Libres"
			else:
				ddbbHealth = "OK"

		if (aibeTest):
			aibe = "KO"
		else:
			aibe = "OK"


		#Servicio SQL
		sql=0
		for process in psutil.process_iter():
			if ("slack" in process.name()):
				sql += 1


		SystemResources = {"ServerName": computername, "Aibe" : aibe, "ddbbHealth" :ddbbHealth, "CpuLoad": AVGProc, "MemLoad" : OS, "CDrive" : volc, "DDrive" : vold, "EDrive" : vole}
		#SystemResources = json.dumps(SystemResources)

		Outputreport = f'''
				<HTML>
				<TITLE>Monitor de estado de {computername} . Version {version}</TITLE>
				<head>
					<meta http-equiv=""refresh"" content=""{refreshTime}"" ></head>
				<BODY background-color:white>
					<H3> Version {version}</H3>
					<H1> Servidor Aibe </H1>
					<H2> Monitor de estado de {computername} </H2>
					<Table border=1 cellpadding=3 cellspacing=3>
						<TR bgcolor=white align=center>
							<TD><B>Estado</B>
							<TD><B>Servidor AibE</B></TD>
							<TD><B>Estado Aibe</B></TD>
							<TD><B>Uso de CPU</B></TD>
							<TD><B>Uso de Memoria</B></TD>
							<TD><B>Uso de Disco C</B></TD>
							<TD><B>Uso de Disco D</B></TD>
							<TD><B>Uso de Disco E</B></TD>'''


		if (monitortype == "CLOUD" ):
			Outputreport += "<TD><B>Espacio para Backup BBDD</B></TD>"

		Outputreport +='''
				<TD><B>Ultimo Test</B></TD>
				<TD><B>Tests Fallidos</B></TD></TR>'''

		if (SystemResources['MemLoad'] >= maxMem) or (SystemResources["Aibe"] == "KO") or (SystemResources["ddbbHealth"] != "OK") or (SystemResources["CDrive"] >= maxDrive) or (SystemResources["DDrive"] >= maxDrive) or (SystemResources["EDrive"] >= maxDrive):
			AibeCount[i] += 1
			AibeStatus[i] = "KO"
			Outputreport += f"<TR><TD align=center bgcolor=red>{AibeStatus[i]}</TD>"
		else:
			AibeCount[i] = 0
			AibeStatus[i] = "OK"
			Outputreport += f"<TR><TD align=center bgcolor=white>{AibeStatus[i]}</TD>"

		if(SystemResources["Aibe"] == "KO"):
			aibecolor = "red"
		else:
			aibecolor = "white"


		if(SystemResources["ddbbHealth"] != "OK"):
			ddbbcolor = "red"
		else:
			ddbbcolor = "white"

		if(SystemResources['MemLoad'] >= maxMem):
			ml = "red"
		else:
			ml = "white"

		if(SystemResources['CpuLoad'] >= maxCpu):
			pl = "red"
		else:
			pl = "white"

		#if(Entry.CpuLoad -ge $maxCpu)   { $pl = "red"} else { $pl = "white"}

		if(SystemResources["CDrive"] >= maxDrive):
			cl = "red"
		else:
			cl = "white"


		if(SystemResources["DDrive"] >= maxDrive):
			dl = "red"
		else:
			dl = "white"

		if(SystemResources["EDrive"] >= maxDrive):
			el = "red"
		else:
			el = "white"

		Outputreport += f'''<TD>{SystemResources["ServerName"]}</TD>
						<TD align=center bgcolor={aibecolor}>{SystemResources["Aibe"]}</TD>
						<TD align=center bgcolor="{pl}">{SystemResources['CpuLoad']}%</TD>
						<TD align=center bgcolor={ml}>{SystemResources['MemLoad']}%</TD>
						<TD align=center bgcolor={cl}>{SystemResources["CDrive"]}%</TD>
						<TD align=center bgcolor={dl}>{SystemResources["DDrive"]}%</TD>
						<TD align=center bgcolor={el}>{SystemResources["EDrive"]}%</TD>'''
		
		if monitortype == "CLOUD":
			Outputreport += f"<TD align=center bgcolor={ddbbcolor}>{SystemResources['ddbbHealth']}</TD>"

		Outputreport += f'''
					<TD align=center>{time.strftime("%x")} {time.strftime("%X")}</TD><TD align=center>{AibeCount[i]}</TD></TR>
				</table>'''

		failed_test = AibeCount[i]

		if (monitortype != "CLOUD" ):
			Outputreport += """
				<H2> Monitor de servicios de $($computername) </H2>
				<Table border=1 cellpadding=3 cellspacing=3>
					<TR bgcolor=white align=center>
						<TD><B>Estado</B>
						<TD><B>Servicio</B></TD>
						<TD><B>Modo de arranque</B></TD>
						<TD><B>Valor</B></TD>
						<TD><B>Ultimo Test</B></TD>
						<TD><B>Tests Fallidos</B></TD>
					</TR>"""
			tempaibeservices=[]
			for Entryads in psutil.win_service_iter():
				if( "advantage" in Entryads.name() or "aibe" in Entryads.name()):
					i += 1
					if ("AUTO" in Entryads.name()) and ("running" !=  Entryads.status()):
						AibeCount[i] += 1
						AibeStatus[i] = "KO"
						Outputreport += f"<TR><TD align=center bgcolor=red>{AibeStatus[i]}</TD>"
					else:
						AibeCount[i] = 0
						AibeStatus[i] = "OK"
						Outputreport += f"<TR><TD align=center bgcolor=white>{AibeStatus[i]}</TD>"
					Outputreport += f"<TD>{Entryads.name()}</TD><TD align=center>{Entryads.start_type()}</TD><TD align=center>{Entryads.status()}</TD><TD align=center>{time.strftime('%x')} {time.strftime('%X')}</TD><TD align=center>{AibeCount[i]}</TD></TR>"
					tempaibeservices.append({
							"status" : "OK",
							"service" : Entryads.name(),
							"start_mode" : Entryads.start_type(),
							"value" : Entryads.status(),
							"last_test" :  f'{time.strftime("%x")} {time.strftime("%X")}',
							"failed_test" : "OK"
					})
					Outputreport += """
						</table>"""
		monitor = open(outfile,'w')
		monitor.write(Outputreport)
		monitor.close()



		######################################################################
		# Proceso de envio de mail con horario para deshabilitar
		#outfile = open(outfile,'r')

		ahora = time.strftime("%x"), time.strftime("%X")
		nowminutes = time.strftime("%M")
		DisableStart = jsonData["vars"]["disablealerts"]["horaini"]*60 + jsonData["vars"]["disablealerts"]["minini"]
		DisableEnd = jsonData["vars"]["disablealerts"]["horafin"]*60 + jsonData["vars"]["disablealerts"]["minfin"]

		if((int(nowminutes) >= int(DisableStart)) and (int(nowminutes) <= DisableEnd) and (SentOk != "ini")):
			# Alerts Disabled
			if("KO" in AibeStatus):
				SentOk = "dis"
			else:
				SentOk = "yes"
		else:
			if(maxCount in AibeCount):
				sendmail (smtpServer, smtpFrom, smtpTo, messageSubject, Outputreport)
				SentOk = "no"

			if((("KO" not in AibeStatus) and (SentOk == "no")) or (SentOk == "ini")):
				prefix = ""
				if (SentOk == "ini"):
					prefix = "ARRANQUE : " + messageSubject
				else:
					prefix = messageSubject

				sendmail(smtpServer, smtpFrom, smtpTo, messageSubject, Outputreport)
				#sendmail (smtpServer, smtpFrom, smtpTo, messageSubject, "<html><body>Prueb de envio de email</body></html>")

				SentOk = "yes"

			if(SentOk == "dis"):
				sendmail(smtpServer, smtpFrom, smtpTo, messageSubject, Outputreport)
				SentOk = "no"

		############################################# Fin envío email #############################################

		######################################## Construcción JSON ########################################
		lasttimetest = f'{time.strftime("%x")} {time.strftime("%X")}'
		dataJson={}
		dataJson["monitor"]=[]
		dataJson["monitor"].append({
				"app_server":{
					"version": str(version),
					"server_name": computername,
					"aibe_status": str(SystemResources["Aibe"]),
					"cpu_usage": str(SystemResources['CpuLoad']),
					"ram_usage": str(SystemResources['MemLoad']),
					"backup_space":  str(SystemResources['ddbbHealth']),
					"last_test": lasttimetest,
					"failed_test":  str(AibeCount[0])
                }
		})
		dataJson["monitor"][0]["app_server"]["disks"]=[]
		dataJson["monitor"][0]["app_server"]["disks"].append({
				"name":  "disk1",
				"location":  "c",
				"disk_usage":  str(SystemResources["CDrive"])
		})
		dataJson["monitor"][0]["app_server"]["disks"].append({
				"name":  "disk2",
				"location":  "d",
				"disk_usage": str(SystemResources["DDrive"])
		})
		dataJson["monitor"][0]["app_server"]["disks"].append({
				"name":  "disk3",
				"location":  "e",
				"disk_usage":  str(SystemResources["EDrive"])
		})
		dataJson["monitor"][0]["pbx_server"]={
				"version":"",
				"server_name":"",
				"systema":{
					"cpus":0,
					"loadaverage":
					{
						"loadavg5min":"",
						"loadavg15min":"",
						"loadavg1min":""
					},
					"cpu_usage":"",
					"ram_usage":"",
					"disks":
					[
						{"name":"disk1","location":"/","disk_usage":""},
						{"name":"disk2","location":"/boot","disk_usage":""},
						{"name":"disk3","location":"/Grabaciones","disk_usage":""}
					]
				},
				"app_pbx":
				{
					"pending_records":"",
					"extensions":"",
					"trunks":
					[
						{"status":"","description":"","name":"","ip":"","ping":""}
					],
					"banned_ip":"",
					"status_asterisk":""
				}
		}

		########### Configurador ############
		'''dataJson["configurador"]={
						"maxmem":maxMem,
						"maxcpu":maxCpu,
						"maxdrive":maxDrive,
						"maxcount":maxCount,
						"refreshtime":refreshTime,
						"sentok":SentOk,
						"outfile":outfile,
						"alert_horaini":jsonData["vars"]["disablealerts"]["horaini"],
						"alert_minini":jsonData["vars"]["disablealerts"]["minini"],
						"alert_horafin":jsonData["vars"]["disablealerts"]["horafin"],
						"alert_minfin":jsonData["vars"]["disablealerts"]["minfin"],
						"pbxname":computername,
						"pbxurl":pbxurl,
						"maxping":maxping,
						"maxpendrec":maxPendRec,
						"smtpserver":smtpServer,
						"smtpuser":smtpUser,
						"smtppass":smtpPass,
						"smtpfrom":smtpFrom,
						"smtpto":smtpTo,
						"messagesubject":messageSubject,
						"computername":computername,
						"geturl":""
		}'''


		dataJson["configurador"]={}
		for configurador in jsonData:
			for configuradorData in jsonData[configurador]:
				if(configuradorData !=  'disablealerts'):
					dataJson["configurador"][configuradorData]=jsonData[configurador][configuradorData]
				else:
					for disablealerts in jsonData[configurador][configuradorData]:
						dataJson["configurador"][disablealerts]=jsonData[configurador][configuradorData][disablealerts]

		dataJson1 = json.dumps(dataJson)

		########### Metodo POST #########

		headers = {
			'Content-Type': 'application/json'
		}
		postParams = {"operation":'insertar', "data":dataJson1}
		#getUrl = 'http://zasysql.aibecloud.com/scripts/sistemamonitor/monitorizacion/datareport.aspx'
		response = post(getUrl, headers=headers, params=postParams)
		print(getUrl)
		#response.raise_for_status()
		########### Fin Metodo POST #########
		#print(dataJson1)

		######################################## Fin Construcción JSON ########################################
		time.sleep(refreshTime)

		#print("Pasaron 10 segundos",j)

##################### Sistema Linux #####################
if (psutil.LINUX):

	while(True):

		i=0

		Outputreport = f'''
			<HTML>
				<TITLE>Monitor de estado de {computername} . Version {version}</TITLE> 
				<head>
				<meta http-equiv=""refresh"" content=""{refreshTime}"" ></head>
				<BODY background-color:white> 
					<H3> Version {version}</H3>'''

		Outputreport += f'''
			<BR><BR><H1>PBX Asociada</H1>
			<H2> Monitor de estado de {computername} </H2> 
			<Table border=1 cellpadding=3 cellspacing=3> 
				<TR bgcolor=white align=center>
					<TD><B>Estado</B>
					<TD><B>Uso de CPU</B></TD>
					<TD><B>Load Average 1m - 5m - 15m </TD>'''
				

		HDDKO = 0
		i += 1
		loadKO = 0

		for HDDStats in psutil.disk_partitions(all=False):
			if 'xvd' in HDDStats.device:
				Outputreport += f"<TD><B>Uso de Disco ({HDDStats.mountpoint})</B></TD>"
				if (psutil.disk_usage(HDDStats.mountpoint).percent) >= maxDrive: HDDKO = 1

		Outputreport +='''
					<TD><B>Ultimo Test</B></TD>
					<TD><B>Tests Fallidos</B></TD> 
				</TR>'''

		load1m = os.getloadavg()[0]
		load5m = os.getloadavg()[1]
		load15m = os.getloadavg()[2]
		ncpus = psutil.cpu_count()
		usagecpu = psutil.cpu_percent(interval=1)

		if (load1m/ncpus >= 0.6) or (load5m/ncpus >= 0.6) or (load15m/ncpus >= 0.6): loadKO = 1

	      
		if ((usagecpu >= maxCpu ) or (HDDKO == 1) or (loadKO == 1)):
			AibeCount[i] += 1
			AibeStatus[i] = "KO"
			Outputreport += f"<TR><TD align=center bgcolor=red>{AibeStatus[i]}</TD>"
		else:
			AibeCount[i] = 0
			AibeStatus[i] = "OK"
			Outputreport += f"<TR><TD align=center bgcolor=white>{AibeStatus[i]}</TD>"

		if (usagecpu >= maxCpu ):
			ppl = "red"
		else:
			ppl = "white"

		if loadKO == 1:
			plo = "red"
		else:
			plo = "white"

		Outputreport += f"""<TD align=center bgcolor={ppl}>{usagecpu}%</TD>
			<TD align=center bgcolor={plo}>{load1m}- {load5m} - {load15m}</TD>"""

		for HDDStats in psutil.disk_partitions(all=False):
			if 'xvd' in HDDStats.device:
				if psutil.disk_usage(HDDStats.mountpoint).percent >= maxDrive:
					Outputreport += f"<TD align=center bgcolor=red >{round(psutil.disk_usage(HDDStats.mountpoint).percent)}</TD>"
				else:
					Outputreport += f"<TD align=center bgcolor=white >{round(psutil.disk_usage(HDDStats.mountpoint).percent)}</TD>"

		timetest = time.strftime("%x"), time.strftime("%X")

		Outputreport += f"<TD align=center>{timetest[0]} {timetest[1]}</TD><TD align=center>{AibeCount[i] }</TD></TR></Table>"

		Outputreport += '''<H2>Estado de troncales</H2>
			<Table border=1 cellpadding=3 cellspacing=3> 
				<TR bgcolor=white align=center>
					<TD>Estado</TD><TD>Nombre</TD><TD>Direccion IP</TD><TD>Ping (ms)</TD><TD>Test Fallidos</TD>
				</TR>'''

		trunks=[]
		for line in open('/etc/asterisk/extensions_additional.conf', 'r'):
			if ('end of [from-trunk-sip' in line):
				trunks.append(line[29:len(line)-8])


		for line in trunks:
			i += 1
			status = subprocess.Popen("/usr/sbin/asterisk -x 'sip show peers' | grep " + line + " | /bin/awk '{{print $6}}'", shell=True, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8')
			nombre = subprocess.Popen("/usr/sbin/asterisk -x 'sip show peers' | grep " + line + " | /bin/awk '{{print $1}}'", shell=True, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8')
			ip= subprocess.Popen("/usr/sbin/asterisk -x 'sip show peers' | grep " + line + " | /bin/awk '{{print $2}}'", shell=True, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8')
			ping = subprocess.Popen("/usr/sbin/asterisk -x 'sip show peers' | grep " + line + " | /bin/awk '{{print $7}}'", shell=True, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8')
			trunkping = int(ping[1:])

			if (trunkping == ""):
				trunkping = "--"
				pingcolor="white"

			if(trunkping < maxping):
				pingcolor="white"
			else:
				pingcolor = "red"

			status = status.rstrip('\n')
			if ((status == "OK") or (status=="Unmonitored")):
				AibeCount[i] = 0
				trunkcolor = "white"
				AibeStatus[i] = "OK"
			else:
				AibeCount[i] += 1
				trunkcolor = "red"
				AibeStatus[i] = "KO"
			
			Outputreport += f"<TR><TD align=center bgcolor={trunkcolor}>{AibeStatus[i]}</TD><TD align=center>{str(nombre)}</TD><td align=center>{str(ip)}</td><td align=center bgcolor={pingcolor}>{trunkping}</td><TD align=center bgcolor=white>{AibeCount[i]}</TD></tr>"
			
			
		Outputreport += """
			</table>
			<H2>Otros datos</H2>
			<Table border=1 cellpadding=3 cellspacing=3> 
				<TR bgcolor=white align=center>
					<TD>Grabaciones pendientes</TD><TD>IPs Bloqueadas</TD><TD>Extensiones creadas</TD><TD>Servicio Asterisk</TD>
				</TR>
			"""

		i += 1

		pendrec=len(glob("/Grabaciones/*.wav"))

		if (pendrec >= maxPendRec):
			AibeCount[i] += 1
			AibeStatus[i] ="KO"
			pendreccolor = "red"
		else:
			AibeCount[i] = 0
			AibeStatus[i] ="OK"
			pendreccolor = "white"

		Outputreport += f"<TD bgcolor={pendreccolor} align=center>{pendrec}</TD>"

		#Banned = subprocess.Popen("/usr/bin/fail2ban-client status asterisk  | /bin/awk -F '-' '{{print $2}}' | /bin/sed 's/^ *//g' | /bin/grep 'IP list' | /bin/awk '{{print $3}}'", shell=True, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8')
		Banned = subprocess.Popen("/usr/bin/fail2ban-client status asterisk  | /bin/awk -F '-' '{{print $2}}' | /bin/sed 's/^ *//g' | /bin/grep 'IP list' | /bin/awk '{{ for (i = 3; i <= NF; i++) print $i \n }}'", shell=True, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8')
		Banned = Banned.replace("\n","<br>")
		if(Banned == ""):
			fail2ban = "Ninguna"
			failcolor = "white"
		else:
			fail2ban = Banned
			failcolor = "white"
		
		Outputreport += f"<TD bgcolor={failcolor} align=center>{fail2ban}</TD>"

		i += 1

		extend = (subprocess.Popen("asterisk -rx 'database showkey voicemail' | /bin/awk '$3==\"novm\" {{print $1,$3}}' | /bin/awk -F '/' '{{print $3}}'", shell=True, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8')).split("\n")

		Outputreport += f"<TD align=center>{len(extend)-1}</TD>"

		processCount=0
		for process in psutil.process_iter():
			if ("asterisk" in process.name()):
				processCount += 1

		if (processCount > 0 ):
			AibeCount[i] = 0
			AibeStatus[i] = "OK"
			astercolor = "white"
		else:
			AibeCount[i] = maxCount
			AibeStatus[i] = "KO"
			astercolor = "red"

		Outputreport += f"<TD align=center bgcolor={astercolor}>{AibeStatus[i]}</TD></TR></Table>"

		Outputreport += "</BODY></HTML>"

		
		monitor = open('html/index1.html','w')
		monitor.write(Outputreport)
		monitor.close()
		
		######################################################################
		# Proceso de envio de mail con horario para deshabilitar
		#outfile = open(outfile,'r')
		
		ahora = time.strftime("%x"), time.strftime("%X")
		nowminutes = time.strftime("%M")
		DisableStart = jsonData["vars"]["disablealerts"]["horaini"]*60 + jsonData["vars"]["disablealerts"]["minini"]
		DisableEnd = jsonData["vars"]["disablealerts"]["horafin"]*60 + jsonData["vars"]["disablealerts"]["minfin"]

		if((int(nowminutes) >= int(DisableStart)) and (int(nowminutes) <= DisableEnd) and (SentOk != "ini")):
	        # Alerts Disabled
			if("KO" in AibeStatus):
				SentOk = "dis"
			else:
				SentOk = "yes"
		else:
			if(maxCount in AibeCount):
				sendmail (smtpServer, smtpFrom, smtpTo, messageSubject, Outputreport)
				SentOk = "no"
		    
			if((("KO" not in AibeStatus) and (SentOk == "no")) or (SentOk == "ini")):
				prefix = ""
				if (SentOk == "ini"):
					prefix = "ARRANQUE : " + messageSubject
				else:
					prefix = messageSubject
		            
				sendmail(smtpServer, smtpFrom, smtpTo, messageSubject, Outputreport)
				#sendmail (smtpServer, smtpFrom, smtpTo, messageSubject, "<html><body>Prueb de envio de email</body></html>")
				SentOk = "yes"

			if(SentOk == "dis"):
				sendmail(smtpServer, smtpFrom, smtpTo, messageSubject, Outputreport)
				SentOk = "no"
		
		#######################################################################


		################## Construcción JSON ################## 
		lasttimetest = f'{time.strftime("%x")} {time.strftime("%X")}'
		dataJson={}
		dataJson["monitor"]=[]
		dataJson["monitor"].append({
							"app_server":{
                                "version":  "0.3.9",
                                "server_name":  computername,
                                "aibe_status":  "",
                                "cpu_usage":  "",
                                "ram_usage":  "",
                                "disks":[
                                          {
                                            "name":  "disk1",
                                            "location":  "c",
                                            "disk_usage":  ""
                                          },
                                          {
                                            "name":  "disk1",
                                            "location":  "d",
                                            "disk_usage":  ""
                                          },
                                          {
                                            "name":  "disk1",
                                            "location":  "e",
                                            "disk_usage":  ""
                                          }
                                        ],
                                "backup_space":  "",
                                "last_test": lasttimetest,
                                "failed_test":  ""
							}
						})


		dataJson["monitor"][0]["pbx_server"]={
				"version":version,
				"server_name":computername
			}

		dataJson["monitor"][0]["pbx_server"]["systema"]={"cpus":ncpus}
		dataJson["monitor"][0]["pbx_server"]["systema"]["loadaverage"]={
						"loadavg5min":str(load1m),
						"loadavg15min":str(load5m),
						"loadavg1min":str(load15m)
					}
		dataJson["monitor"][0]["pbx_server"]["systema"]["cpu_usage"] =str(usagecpu)
		dataJson["monitor"][0]["pbx_server"]["systema"]["ram_usage"] =""

		dataJson["monitor"][0]["pbx_server"]["systema"]["disks"] =[]
		diskCount=1
		for HDDStats in psutil.disk_partitions(all=False):
			if 'xvd' in HDDStats.device:
				dataJson["monitor"][0]["pbx_server"]["systema"]["disks"].append({
						"name":f"disk{diskCount}",
						"location":HDDStats.mountpoint,
						"disk_usage": str(round(psutil.disk_usage(HDDStats.mountpoint).percent))

					})
				diskCount+=1

		dataJson["monitor"][0]["pbx_server"]["app_pbx"]={
				"pending_records":str(pendrec),
				"extensions":str(len(extend)-1)
			}
		dataJson["monitor"][0]["pbx_server"]["app_pbx"]["trunks"]=[]
		tk=0
		for line in trunks:
			status = subprocess.Popen("/usr/sbin/asterisk -x 'sip show peers' | grep " + line + " | /bin/awk '{{print $6}}'", shell=True, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8').replace("\n","")
			nombre = subprocess.Popen("/usr/sbin/asterisk -x 'sip show peers' | grep " + line + " | /bin/awk '{{print $1}}'", shell=True, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8').replace("\n","")
			ip= subprocess.Popen("/usr/sbin/asterisk -x 'sip show peers' | grep " + line + " | /bin/awk '{{print $2}}'", shell=True, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8').replace("\n","")
			ping = subprocess.Popen("/usr/sbin/asterisk -x 'sip show peers' | grep " + line + " | /bin/awk '{{print $7}}'", shell=True, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8').replace("\n","")
			#trunkping = int(ping[1:])
			dataJson["monitor"][0]["pbx_server"]["app_pbx"]["trunks"].append({
					"status":status,
					"description":f"tk{tk}",
					"name":nombre,
					"ip":ip,
					"ping":ping[1:]
				})
			tk+=1

		baneada = subprocess.Popen("/usr/bin/fail2ban-client status asterisk  | /bin/awk -F '-' '{{print $2}}' | /bin/sed 's/^ *//g' | /bin/grep 'IP list' | /bin/awk '{{ for (i = 3; i <= NF; i++) print $i \n }}'", shell=True, stdout=subprocess.PIPE).communicate()[0].decode('UTF-8').replace("\n"," ")
		dataJson["monitor"][0]["pbx_server"]["app_pbx"]["banned_ip"]=baneada

		if (processCount > 0 ):
			dataJson["monitor"][0]["pbx_server"]["app_pbx"]["status_asterisk"]="OK"
		else:
			dataJson["monitor"][0]["pbx_server"]["app_pbx"]["status_asterisk"]="KO"

		########### Configurador ############

		dataJson["configurador"]={}
		for configurador in jsonData:
			for configuradorData in jsonData[configurador]:
				if(configuradorData !=  'disablealerts'):
					dataJson["configurador"][configuradorData]=jsonData[configurador][configuradorData]
				else:
					for disablealerts in jsonData[configurador][configuradorData]:
						dataJson["configurador"][disablealerts]=jsonData[configurador][configuradorData][disablealerts]
	
		dataJson1 = json.dumps(dataJson)
		#postParams = {"operation":'insertar', "data":dataJson1}
		
		#postParams1=json.dumps(postParams)

		########### Metodo POST #########
	
		headers = {
			'Content-Type': 'application/json'
		}
		postParams = {"operation":'insertar', "data":dataJson1}
		#getUrl1 = 'http://zasysql2.aibecloud.com/scripts/sistemamonitor/monitorizacion/datareport.aspx'
		try:
			response = post(getUrl, headers=headers, params=postParams)
		except:
			log = open ('/var/log/monitor.log','a')
			log.write(f'---------------------------------------------------------------------------------------------------\n')
			log.write(f'{time.strftime("%b %d %y")} {time.strftime("%X")} -- Ha ocurrido un error al conectarse a {getUrl1}\n')
			log.close()
		#response.raise_for_status()
		########### Fin Metodo POST #########
				
		'''with open('monitorpbx/data.json', 'w') as file:
			json.dump(dataJson, file, indent=4)'''
			#json.dump(data, file)

		time.sleep(refreshTime)
		#print(messageSubject)
		#print(f"Pasaron {refreshTime} segundos",j)
