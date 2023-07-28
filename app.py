from flask import Flask,render_template,request,send_file,session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os,io
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
app.app_context().push()

class mol_acetylcholinesterase(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    filename = db.Column(db.String(50))
    data = db.Column(db.String)
    results = db.Column(db.String)  # new field for storing the results
    headings = db.Column(db.String)

class mol_vegfr2(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    filename = db.Column(db.String(50))
    data = db.Column(db.String)
    results = db.Column(db.String)  # new field for storing the results
    headings = db.Column(db.String)

class mol_bace1(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    filename = db.Column(db.String(50))
    data = db.Column(db.String)
    results = db.Column(db.String)  # new field for storing the results
    headings = db.Column(db.String)

class mol_hiv1rt(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    filename = db.Column(db.String(50))
    data = db.Column(db.String)
    results = db.Column(db.String)  # new field for storing the results
    headings = db.Column(db.String)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/method/')
def methods():
    return render_template('method.html')

@app.route('/references/')
def references():
    return render_template('references.html')

@app.route('/acetylcholinesterase/')
def acetylcho():    
    return render_template('acetylcho.html')

@app.route('/vegfr2/')
def vegfr2():    
    return render_template('vegfr2.html')

@app.route('/bace1/')
def bace1():
    return render_template('bace1.html')

@app.route('/hiv1rt/')
def hiv1rt():
    return render_template('hiv1rt.html')

@app.route('/compounds/')
def compounds():
    return render_template('compounds.html')

@app.route('/about/')
def about():
    return render_template('about.html')


@app.route('/upload/',methods = ['POST'])
def upload_file():
    data = request.json
    filecontent = data.get('fileContent')
    filename = data.get('filename')
    compound_name = data.get('compound_name')
    session['valid_results'] = True

    compound_models = {
        "acetylcholinesterase": mol_acetylcholinesterase,
        "vegfr2": mol_vegfr2,
        "bace1":mol_bace1,
        "hiv1rt":mol_hiv1rt,
    }
    compounds_model = compound_models.get(compound_name)
    upload = compounds_model(filename=filename, data=filecontent)
    from utils import model_predict
    df = model_predict(compound_name,filecontent,str(upload.id))
    if df.empty:
        upload.results = "Invalid"
        upload.headings = "Invalid"
        session['valid_results'] = False
    else:
        df['Predicted IC50 value (nM)'] = df['Predicted IC50 value (nM)'].astype('float64').round(3).sort_values('Predicted IC50 value (nM)')
        upload.results = json.dumps(df.values.tolist())
        upload.headings = json.dumps(list(df))

    db.session.add(upload)
    db.session.commit()
    
    session['id'] = str(upload.id)
    session['name'] = compound_name

    return "file successfully uploaded"


@app.route('/results/')
def results():
    id = session.get('id',[])
    name = session.get('name',[])
    upload = db.session.query(eval('mol_'+session.get('name',[]))).filter_by(id=id).first()

    names_list = {
        "acetylcholinesterase":"Acetylcholinesterase",
        "vegfr2":"VEGF Receptor-2",
        "bace1":"Beta-Secretase 1",
        "hiv1rt":"HIV-1 RT"
    }
    
    if upload.results == "Invalid":
        return render_template('results.html', name=names_list.get(name))
    
    headings = json.loads(upload.headings)
    data = json.loads(upload.results)
    
    session.pop('id',None)
    session.pop('valid_results',None)

    return render_template('results.html', name=names_list.get(name),headings=headings, data=data, id=id, file_download = "Download csv file here")


@app.route('/download/<variable>/')
def download_file(variable):
    name = session.get('name',[])
    session.pop('name',None)
    
    upload = db.session.query(eval('mol_'+name)).filter_by(id=variable).first()
    headings = json.loads(upload.headings)
    data = json.loads(upload.results)
    df = pd.DataFrame(data=data, columns=headings)

    file_path = 'models/'+name+'/data/'+str(variable)+'.csv'
    df.to_csv(file_path)
    
    return_data = io.BytesIO()
    with open(file_path, 'rb') as fo:
        return_data.write(fo.read())
    return_data.seek(0)
    os.remove(file_path)
        
    return send_file(return_data, mimetype='csv', as_attachment=True,download_name = file_path)


if __name__=='__main__':
    app.run(debug=False)