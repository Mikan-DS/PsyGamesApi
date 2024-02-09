import datetime

from flask import Flask, request, jsonify, abort, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///PsyTestApi.db'
db = SQLAlchemy(app)



class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_name = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    ip = db.Column(db.String(80), nullable=False)
    end_time = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    duration = db.Column(db.Integer, nullable=False)
    parameters = db.relationship('TestResultParameter', backref='test_result', lazy=True)

    def __init__(self, project_name, name, ip, duration, result_parameters):
        self.project_name = project_name
        self.name = name
        self.ip = ip
        self.duration = duration
        self.parameters = self.create_parameters(result_parameters)

    def create_parameters(self, result_parameters):
        parameters = []
        pairs = result_parameters.split(';')
        for pair in pairs:
            pair = pair.strip()
            if not pair:
                continue
            name, value = pair.split(':')
            parameter = TestResultParameter(self.id, name.strip(), value.strip())
            parameters.append(parameter)
        return parameters

    def __repr__(self):
        return '<TestResult %r>' % self.project_name

    def as_dict(self):
        return {
            'id': self.id,
            'project_name': self.project_name,
            'name': self.name,
            'ip': self.ip,
            'end_time': self.end_time,
            'duration': self.duration,
            'result_parameters': {
                parameter.name: parameter.value for parameter in self.parameters
            }
        }


class TestResultParameter(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    test_result_id = db.Column(db.Integer, db.ForeignKey('test_result.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    value = db.Column(db.String(500), nullable=False)

    def __init__(self, test_result_id, name, value):
        self.test_result_id = test_result_id
        self.name = name
        self.value = value

    def __repr__(self):
        return '<TestResultParameter %r>' % self.name

# @app.route('/', methods=['GET'])
# def index():
#     return "Hello World!"


@app.route('/api/add-result', methods=['POST'])
def add_result():

    result = dict(request.args)
    result["ip"] = request.remote_addr
    result["duration"] = int(result["duration"])

    try:
        ts = TestResult(**result)
        db.session.add(ts)
        db.session.commit()

        return jsonify(ts.as_dict())

    except Exception as e:
        raise e

        abort(400, 'Неверный результат теста')

@app.route('/admin/view-results', methods=['GET'])
def psytest_view_results():

    test_results = TestResult.query.all()
    data = {}
    for result in test_results:
        if result.project_name not in data:
            data[result.project_name] = []
        data[result.project_name].append(result.as_dict())
    return render_template('view-test-results.html', data=data)


with app.app_context():
    db.create_all()

if __name__ == '__main__':

    app.run(debug=True)
