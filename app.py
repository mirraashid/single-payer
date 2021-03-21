from flask import Flask, render_template, session
from flask_restful import Resource, Api, reqparse
import requests, sys, uuid, os
from termcolor import colored
import constants as creds
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.sql import func


app = Flask(__name__)
api = Api(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1@localhost/singlepayer'
# db = SQLAlchemy(app)


#DB model for singlepayer user data
# class User(db.Model):
# 	__tablename__ = 'userData'
# 	id = db.Column(db.Integer, primary_key=True)
# 	dateTime = db.Column(db.DateTime(timezone=True), default=func.now())
# 	email = db.Column(db.String(120))
# 	inputValues = db.Column(db.String(2500))
# 	outputValues = db.Column(db.String(2500))
    
# 	def __init__(self, email, inputValues, outputValues):
# 		self.email = email
# 		self.inputValues = inputValues
# 		self.outputValues = outputValues

def getToken():
    #message_terminal("attempting to obtain token from MS servers")

    url = "https://login.microsoftonline.com/" + creds.GRAP_API['tenantId'] + "/oauth2/v2.0/token"

    headers = {'Content-Type': 'application/x-www-form-urlencoded'} 
    
    payload = {
        'client_id': creds.GRAP_API['clientId'],
        'client_secret': creds.GRAP_API['clientSecret'],
        'scope': 'https://graph.microsoft.com/.default',
        'grant_type' : 'client_credentials',
    }
    

    response = requests.request("POST", url, headers=headers, data = payload)
    access_token = response.json()['access_token']
	#message_terminal("access token returned as ", access_token)
    return access_token

def startSession(access_token):
    #message_terminal("now attempting to start session with bearer token")

	sessionURL = creds.GRAP_API['baseUrl'] + 'workbook/createSession'

	headers = {
        'Authorization':'Bearer '+access_token,
		'Content-Type':'application/json',
		'scope':'Files.ReadWrite.all'
        }

	body = '{"persistChanges": false}'
	sessionRequest = requests.post(sessionURL, headers=headers, data=body)
	response = sessionRequest.json()
	sessionId = sessionRequest.json()['id']
	#message_terminal("response was: ", response)
	#message_terminal("with a session ID of: ", session_id)
	return sessionId

def subData(bearerTolken, sessionID):
	#message_terminal("now gathering user input data")
	parser = reqparse.RequestParser()
	#add to body? add to body
	parser.add_argument('spPlan')
	parser.add_argument('hpPremium')
	parser.add_argument('timeframe')
	parser.add_argument('epc')
	parser.add_argument('epcTimeFrame')
	parser.add_argument('typeOfWork')
	parser.add_argument('oop')
	parser.add_argument('oopLongTerm')
	parser.add_argument('householdSize')
	parser.add_argument('householdIncome')
	parser.add_argument('deductible')
	parser.add_argument('shareOfCostHospital')
	parser.add_argument('shareOfCostHospitalType')
	parser.add_argument('annualOop')
	args = parser.parse_args()
	headers = {'Authorization':'Bearer '+bearerTolken,
		'Content-Type':'application/json',
		'scope':'Files.ReadWrite.all',
		'workbook-session-id': sessionID,
		}
	body = '{"values": [[\''+str(args['spPlan'])+'\'], ['+str(args['hpPremium'])+'], [\''+str(args['timeframe'])+'\'], [\''+str(args['epc'])+'\'], [\''+str(args['epcTimeFrame'])+'\'], [\''+str(args['typeOfWork'])+'\'], ['+str(args['oop'])+'], ['+str(args['oopLongTerm'])+'], ['+str(args['householdSize'])+'], ['+str(args['householdIncome'])+'], ['+str(args['deductible'])+'], ['+str(args['shareOfCostHospital'])+'], [\''+str(args['shareOfCostHospitalType'])+'\'], ['+str(args['annualOop'])+']]}'
	print("now sending user input data to Graph API, with the following header and body: ", headers, body)

	subURL = creds.GRAP_API['baseUrl'] + 'workbook/worksheets(\'I-O\')/range(address=\'C3:C16\')'
	subReq = requests.patch(subURL, headers=headers, data=body)

	if subReq.status_code == 200:
		print(colored("Success", "green"))
	else:
		#error_message = "Error, code" + str(subReq.status_code)
		error_message = "Error, code" + str(subReq.json())
		print(colored(error_message, "red"))


	return subReq.content, 200


def retCalcs(bearerTolken, sessionID):
	#message_terminal("now retreiving the result data from Graph API")

	retURL = creds.GRAP_API['baseUrl'] + 'workbook/worksheets(\'I-O\')/range(address=\'C23:C32\')'
	headers = {'Authorization':'Bearer '+bearerTolken,
		'Content-Type':'application/json',
		'scope':'Files.ReadWrite.all',
		'workbook-session-id': sessionID,
		}
	r = requests.get(retURL, headers=headers)

	if r.status_code == 200:
		print(colored("Success", "green"))
	else:
		error_message = "Error, code" + str(r.status_code)
		print(colored(error_message, "red"))

	return r.json()
    

def processSubmission():
	#process input submission and response collection
    token = getToken()
    sessionID = startSession(token)
    subData(token, sessionID)
    results = retCalcs(token, sessionID)

	#save user data

    parser = reqparse.RequestParser()
    print(parser)
    #print(session['sessionId'])
    return results, 200

class ProcessUserSubmission(Resource):
    def post(self):
        return processSubmission()

#List application routes and their respective templates
@app.route('/')
def index():
	# dbQuery = User('mirr1621@gmail.com', 'jkhsdbhjkasbd', 'sadsadasd')
	# db.session.add(dbQuery);
	# db.session.commit()
	# if 'sessionId' not in session:
	# 	session['sessionId'] = uuid.uuid1()
	# 	print(session['sessionId'])
	return render_template('index.html')


#List your APi's and their respective handlers
api.add_resource(ProcessUserSubmission, '/singlePayer/fetch/calc')

if __name__ == '__main__':
	#app.secret_key = os.urandom(24)
	# db.create_all()
	app.run(debug=True)