from wsgi import db

class Dataset(db.Model):
    datasetId = db.Column(db.String, primary_key=True)
    endpoint = db.Column(db.String)
    PID = db.Column(db.Integer)
    bigNumber = db.Column(db.Boolean)
    decimalDigits = db.Column(db.Integer)
    integerDigits = db.Column(db.Integer)
    negativeNumber = db.Column(db.Boolean)
    ZP = db.Column(db.Boolean)

    def __init__(self, datasetId, endpoint, PID, bigNumber, decimalDigits, integerDigits, negativeNumber, ZP):
        self.datasetId = datasetId
        self.endpoint = endpoint
        self.PID = PID
        self.bigNumber = bigNumber
        self.decimalDigits = decimalDigits
        self.integerDigits = integerDigits
        self.negativeNumber = negativeNumber
        self.ZP = ZP

    def __repr__(self):
        return '<datasetId %r>' % self.datasetId


class Workflow(db.Model):
    workflowName = db.Column(db.String, primary_key=True)
    endpoint = db.Column(db.String)
    PID = db.Column(db.Integer)
    bigNumber = db.Column(db.Boolean)
    decimalDigits = db.Column(db.Integer)
    integerDigits = db.Column(db.Integer)
    negativeNumber = db.Column(db.Boolean)
    ZP = db.Column(db.Boolean)

    def __init__(self, workflowName, endpoint, PID, bigNumber, decimalDigits, integerDigits, negativeNumber, ZP):
        self.workflowName = workflowName
        self.endpoint = endpoint
        self.PID = PID
        self.bigNumber = bigNumber
        self.decimalDigits = decimalDigits
        self.integerDigits = integerDigits
        self.negativeNumber = negativeNumber
        self.ZP = ZP

    def __repr__(self):
        return '<workflowName %r>' % self.workflowName


class Pod(db.Model):
    workflowName = db.Column(db.String, primary_key=True)
    PID = db.Column(db.Integer)
    ipAddr = db.Column(db.String)

    def __init__(self, workflowName, PID, ipAddr):
        self.workflowName = workflowName
        self.PID = PID
        self.ipAddr = ipAddr

    def __repr__(self):
        return '<Pod ip %r>' % self.ipAddr


class Jiff_Server(db.Model):
    workflowName = db.Column(db.String, primary_key=True)
    ipAddr = db.Column(db.String)

    def __init__(self, workflowName, ipAddr):
        self.workflowName = workflowName
        self.ipAddr = ipAddr

    def __repr__(self):
        return '<Jiff ip %r>' % self.ipAddr