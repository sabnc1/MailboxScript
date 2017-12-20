import json
from email.header import decode_header
import base64
import hashlib
import os
import gzip
import shutil
import zipfile
import os,time
from time import sleep
import uu

filepath = "/home/knackle/Maildir/new"
#currentDict = dict([(f,None) for f in os.listdir(filepath)])
currentDict = dict()
#Notes
#Figure out how to determine end of file without a boundary at the end
#@
#
#
#
#

while 1:
	sleep(1)
	newDict = dict([(f,None) for f in os.listdir(filepath)])
	added = [f for f in newDict if not f in currentDict]
	removed = [f for f in currentDict if not f in newDict]
	for key in added:
		DictionaryOutput = {}
		boundaries = []
		Field = ""
		Body = ""
		PastBoundary = False
		MessageBody = ""
		MessageBodyFlag = False
		Type = ""
		Disposition = ""
		Encoding = ""
		MessageFlag = False
		DataFlag = False
		SinglePartAndHeadersDone = False
		filename = ""
		AttachmentCount = 0
		IsMultipart = False
		singlePartFileWritten=False
		if added: 
			print key
		infile = open(filepath+"/"+key, "r")
		outfile = open("ParserOutput.json" , "a+")
		with infile as f:
			for line in f:

				if not PastBoundary:
					operator = line.find(":")
					if SinglePartAndHeadersDone:
						if singlePartFileWritten:
							if Encoding=="base64" or Encoding == "BASE64":
								attachmentFile.write(base64.standard_b64decode(line))
							else:
								attachmentFile.write(line)
							
						elif Encoding.lower()=="base64":
							line = base64.standard_b64decode(line)
							MessageBody+=line
							DictionaryOutput.update({"Content-Type":Type})
							DictionaryOutput.update({"Content-Disposition":Disposition})
							DictionaryOutput.update({"Content-Transfer-Encoding":Encoding})
						else:
							MessageBody+=line
							DictionaryOutput.update({"Content-Type":Type})
							DictionaryOutput.update({"Content-Disposition":Disposition})
							DictionaryOutput.update({"Content-Transfer-Encoding":Encoding})
					elif any(key in line for key in boundaries):
						PastBoundary = True
					elif line.strip()=="" and not IsMultipart:
						SinglePartAndHeadersDone = True	
						if Disposition.lower().find("filename")!=-1:
							FilenameIndex = Disposition.find("filename")
							filenameNotDecoded = Disposition.strip()[FilenameIndex+10:-1]
							filename = decode_header(filenameNotDecoded)[0][0] + ""
							attachmentFile = open(filename,"w+")
							singlePartFileWritten = True				
					elif line[:1]=="\t"or line[:1]==" ":
						Body += line.strip()
						if Field=="Content-Type":
							Type=Body
						elif Field=="Content-Disposition":
							Disposition=Body
						elif Field=="Content-Transfer-Encoding":
							Encoding=Body												
						if Field in DictionaryOutput:						
							DictionaryOutput.update({Field:Body})
					elif operator!=-1:
						Field = line[:operator]
						Body = line.strip()[operator+2:]
						if Field.find(" ")!=-1:
							MessageBody += line
						elif Field.lower()=="mime-version":
							pass
						elif Field=="Content-Disposition" :
							Disposition = Body
						elif Field=="Content-Transfer-Encoding":
							Encoding = Body	
						elif Field=="Content-Type":
							if Body[:9].lower()=="multipart":
								IsMultipart=True
								boundaryIndex=Body.lower().find("boundary")
								while boundaryIndex==-1:
									Body = next(f)
									boundaryIndex = Body.lower().find("boundary")
								boundaries.append(Body[boundaryIndex+10:-3])
							else:
								Type = Body
						else:
							DictionaryOutput.update({Field:Body})
					else:
						
						if Disposition.lower().find("filename")!=-1:
							FilenameIndex = Disposition.find("filename")
							filenameNotDecoded = Disposition.strip()[FilenameIndex+10:-1]
							filename = decode_header(filenameNotDecoded)[0][0] + ""
							attachmentFile = open(filename,"w+")							
							if Encoding=="base64" or Encoding == "BASE64":
								attachmentFile.write(base64.standard_b64decode(line))
							else:
								attachmentFile.write(line)
							
						elif Encoding.lower()=="base64":
							line = base64.standard_b64decode(line)
						MessageBody+=line				


						
				else:
					if any(key in line for key in boundaries):  #End of file/Message can close file and do necessary operations here. Close file. Add to Dictionary. Get hases
						#if Encoding =="x-uuencode":
							#try:
								#Not working works on command line with same file. Might be something to do with the library. Commenting out to work on other things
			##					print attachmentFile								
			#					uu.decode(attachmentFile,attachmentFile)
								
							#except uu.Error:
							#	pass
						if DataFlag: #if file written
							AttachmentCount+=1
							sha256 = hashlib.new('sha256')
							sha1 = hashlib.new('sha1')
							md5 = hashlib.new('md5')
							attachmentFile.seek(0)
							sha256.update(attachmentFile.read())
							attachmentFile.seek(0)
							sha1.update(attachmentFile.read())
							attachmentFile.seek(0)
							md5.update(attachmentFile.read())
							fileHash = sha256.hexdigest()
							attachmentFile.close
							with zipfile.ZipFile(fileHash + ".zip", 'w') as fOutput:
								fOutput.write(attachmentFile.name)
								fOutput.close()
							DictionaryForFile={"Filename":attachmentFile.name,"FileType": Type, "Content-Transfer-Encoding":Encoding, "MD5":md5.hexdigest(),"SHA1":sha1.hexdigest(), "SHA256":sha256.hexdigest(),"Content-Disposition":Disposition} 
							os.remove(attachmentFile.name)
							DictionaryOutput.update({"File"+`AttachmentCount`:DictionaryForFile})
						
						DataFlag = False
						MessageFlag = False
						Type = ""
						Disposition = ""
						Encoding = ""
					elif DataFlag:
						if Encoding=="base64" or Encoding == "BASE64":
							attachmentFile.write(base64.standard_b64decode(line))
						else:
							attachmentFile.write(line)
						
					elif MessageFlag:
						MessageBody +=line
					elif line.strip()=="":
						if Disposition.lower().find("filename")!=-1:
							FilenameIndex = Disposition.find("filename")
							filenameNotDecoded = Disposition.strip()[FilenameIndex+10:-1]
							filename = decode_header(filenameNotDecoded)[0][0] + ""
							DataFlag = True
							attachmentFile = open(filename,"w+")
						elif Type[:10].lower()=="text/plain":
							MessageFlag = True
						elif Type[:9].lower()=="text/html":
							MessageFlag = True
					else:
						operator = line.find(":")
						Field = line[:operator]
						Body = line.strip()[operator+2:]
						if line.strip()[-1]==";":
							line = next(f)
							Body+=line.strip()
						if Field=="Content-Type":
							Type=Body
							if Body[:9].lower()=="multipart":
								boundaryIndex=Body.lower().find("boundary")
								while boundaryIndex==-1:
									Body = next(f)
									boundaryIndex = Body.lower().find("boundary")
								boundaries.append(Body[boundaryIndex+10:-3])
						elif Field=="Content-Disposition":
							Disposition = Body
							if line.strip()[:-1]==";":
								line = next(f)
								Body+=line
							
						elif Field=="Content-Transfer-Encoding":
							Encoding = Body
							if line.strip()[:-1]==";":
								line = next(f)
								Body+=line
					
		if singlePartFileWritten:
			sha256 = hashlib.new('sha256')
			sha1 = hashlib.new('sha1')
			md5 = hashlib.new('md5')
			attachmentFile.seek(0)
			sha256.update(attachmentFile.read())
			attachmentFile.seek(0)
			sha1.update(attachmentFile.read())
			attachmentFile.seek(0)
			md5.update(attachmentFile.read())
			fileHash = sha256.hexdigest()
			attachmentFile.close
			with zipfile.ZipFile(fileHash + ".zip", 'w') as fOutput:
				fOutput.write(attachmentFile.name)
				fOutput.close()
			DictionaryForFile={"Filename":attachmentFile.name,"FileType": Type, "Content-Transfer-Encoding":Encoding, "MD5":md5.hexdigest(),"SHA1":sha1.hexdigest(), "SHA256":sha256.hexdigest(), "Content-Disposition": Disposition} 
			os.remove(attachmentFile.name)
			DictionaryOutput.update({"File"+`AttachmentCount`:DictionaryForFile})
		
		#Do this for every file in email library
		DictionaryOutput.update({"Message Body": MessageBody})		
		print json.dumps(DictionaryOutput, ensure_ascii=False)
		#print MessageBody	
		outfile.write(json.dumps(DictionaryOutput, ensure_ascii=False))
		outfile.write("\n")
		outfile.close()
	currentDict = newDict
