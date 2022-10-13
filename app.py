from flask import Flask, render_template, request

from elasticsearch import Elasticsearch
#from utils import *
import json
import nltk
#nltk.download('punkt')
import json
import re
import glob
import os
import pandas as pd

from io import StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser





def cv_contenu(cvPDF):
	output_string = StringIO()
	with open(cvPDF, 'rb') as in_file:
		parser = PDFParser(in_file)
		doc = PDFDocument(parser)
		rsrcmgr = PDFResourceManager()
		device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
		interpreter = PDFPageInterpreter(rsrcmgr, device)
		for page in PDFPage.create_pages(doc):
			interpreter.process_page(page)
	#print(output_string.getvalue())
	return output_string.getvalue()







def get_name(txt):
	u = ""
	pattern = re.compile("[A-Z][a-z]+\s[A-Z]+")
	for s in nltk.sent_tokenize(txt):
		s = s.strip()
		for u in s.split("\n"):
			if pattern.match(str(u)):
				return u

def langages_prog(txt):
	languages = ""
	#print(txt)
	if "Programmation :" in txt:
		languages=txt.split('Programmation :')[1].split('.')[0].split(",")
		#languages[-1] = languages[-1].split(".")[0]
		for i in range(len(languages)):
			languages[i] = languages[i].strip()
		return languages
	elif "Programmation:" in txt:
		languages=txt.split('Programmation:')[1].split('.')[0].split(",")
		#languages[-1] = languages[-1].split(".")[0]
		for i in range(len(languages)):
			languages[i] = languages[i].strip()
		return languages
def get_email(txt):
	email = ""
	pattern = re.compile("^\w+([-+.']\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$")
	for word in txt.split():
		if pattern.match(str(word)):
			email = word
			return email
			
def num_tel(txt):
	num_tel = ""
	pattern = re.compile("^(?:(?:\+|00)33[\s.-]{0,3}(?:\(0\)[\s.-]{0,3})?|0)[1-9](?:(?:[\s.-]?\d{2}){4}|\d{2}(?:[\s.-]?\d{3}){2})$")
	for word in txt.split():
		if pattern.match(str(word)):
			num_tel = word
			return num_tel

			
os.chdir(os.getcwd()+'/cvtheque')
files=glob.glob("*.pdf")
cv_list=[]
	
for f in files:
	cv_list.append(f)


elastic=Elasticsearch(hosts=["127.0.0.1"])
if elastic.indices.exists(index="cv"):
	elastic.indices.delete(index="cv", ignore=[400, 404])



for cv in cv_list:
	text = cv_contenu(cv)
	#print(text)
	prog = ""
	name = ""
	email = ""
	tel = ""
	if langages_prog(text):
		prog = langages_prog(text)
		#print("Langages de programmation : "+ str(prog))
	if get_name(text):
		name = get_name(text)
		#print("Nom : "+name)
	if get_email(text):
		email = get_email(text)
		#print("E-mail : "+email)
	if num_tel(text):
		tel = num_tel(text)
		#print("Tel : "+num_tel)
	response = elastic.index(index="cv", doc_type='books', document=json.dumps({"Fichier":os.getcwd()+"/"+cv, "Name":name,"Email":email,"Tel":tel,"Programmation":prog}))
	
os.chdir('..')



app = Flask(__name__)

@app.route('/')
def index():
	return render_template('main_page.html')

@app.route('/', methods=['POST'])
def my_form_post():
    lang = request.form['text']
    payload = json.dumps({
  "query": {
    "match": {
      "Programmation": lang 
    }
  }
})
    elastic_client = Elasticsearch(hosts=["127.0.0.1"])
    response=elastic_client.search(index="cv", body=payload)
    fichiers = []
    for h in response["hits"]["hits"]:
    	fichiers.append("<a href='file://" + h["_source"]["Fichier"] + "'> file://" + h["_source"]["Fichier"] + "</a>")
    returned = "\n".join(fichiers)
    return  returned
